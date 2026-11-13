import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Client Java de l'API MaintAI (TP2) : la même requête que la page web, curl.exe ou les tests.
 * L'API ne sait pas qui l'appelle ; seul le contrat compte (POST JSON /v1/predict + en-tête X-API-Key).
 *
 * Compilation et lancement (JDK 11 ou plus, aucune bibliothèque externe) :
 *   javac MaintaiClient.java
 *   set MAINTAI_API_KEY=votre-cle                      (PowerShell : $env:MAINTAI_API_KEY="votre-cle")
 *   java MaintaiClient 72 6 85 15000                   (température, vibration, charge, heures)
 *   java MaintaiClient --file ..\releve.json           (le corps lu dans un fichier JSON)
 * Variables facultatives : MAINTAI_URL (défaut http://localhost:8000).
 */
public class MaintaiClient {

    // HTTP/1.1 : par défaut Java tente une mise à niveau HTTP/2 en clair (h2c), qu'uvicorn refuse (400)
    private final HttpClient http = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(5))
            .build();
    private final String baseUrl;
    private final String apiKey;

    public MaintaiClient(String baseUrl, String apiKey) {
        this.baseUrl = baseUrl.replaceAll("/+$", "");
        this.apiKey = apiKey;
    }

    /** Envoie un relevé (déjà en JSON) ; renvoie la réponse brute (code + corps). */
    public HttpResponse<String> predict(String readingJson) throws Exception {
        HttpRequest.Builder req = HttpRequest.newBuilder(URI.create(baseUrl + "/v1/predict"))
                .timeout(Duration.ofSeconds(10))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(readingJson));
        if (apiKey != null && !apiKey.isBlank()) {
            req.header("X-API-Key", apiKey);  // la clé voyage dans un en-tête, jamais dans l'URL
        }
        return http.send(req.build(), HttpResponse.BodyHandlers.ofString());
    }

    static String readingJson(double temperature, double vibration, double load, double hours) {
        return String.format(Locale.ROOT,
                "{\"temperature_c\": %s, \"vibration_mm_s\": %s, \"load_pct\": %s, \"runtime_hours\": %s}",
                temperature, vibration, load, hours);
    }

    /** Lecture minimale d'un champ du JSON de réponse (pas de bibliothèque JSON nécessaire). */
    static String field(String json, String name) {
        Matcher m = Pattern.compile("\"" + name + "\"\\s*:\\s*(\"[^\"]*\"|[^,}\\]]+)").matcher(json);
        return m.find() ? m.group(1).replace("\"", "").trim() : null;
    }

    public static void main(String[] args) throws Exception {
        String body;
        if (args.length == 2 && args[0].equals("--file")) {
            body = Files.readString(Path.of(args[1]));
        } else if (args.length == 4) {
            body = readingJson(Double.parseDouble(args[0]), Double.parseDouble(args[1]),
                    Double.parseDouble(args[2]), Double.parseDouble(args[3]));
        } else {
            System.err.println("Usage : java MaintaiClient <temperature_c> <vibration_mm_s> <load_pct> <runtime_hours>");
            System.err.println("        java MaintaiClient --file releve.json");
            System.exit(2);
            return;
        }

        String url = System.getenv().getOrDefault("MAINTAI_URL", "http://localhost:8000");
        MaintaiClient client = new MaintaiClient(url, System.getenv("MAINTAI_API_KEY"));

        HttpResponse<String> r;
        try {
            r = client.predict(body);
        } catch (java.net.ConnectException | java.net.http.HttpConnectTimeoutException e) {
            System.err.println("API injoignable (" + url + ") : uvicorn est-il lancé ?");
            System.exit(1);
            return;
        }

        if (r.statusCode() != 200) {
            System.err.println("Erreur " + r.statusCode() + " : " + r.body());
            System.exit(1);
        }
        double proba = Double.parseDouble(field(r.body(), "failure_probability"));
        boolean alert = Boolean.parseBoolean(field(r.body(), "alert"));
        System.out.printf(Locale.ROOT, "Probabilité de panne : %d %% (%s, seuil %s)%n",
                Math.round(proba * 100), alert ? "ALERTE" : "normal", field(r.body(), "threshold"));
    }
}
