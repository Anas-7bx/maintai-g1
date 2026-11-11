# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** G1  ·  **Membres :** Moad Bakouch  ·  **Date :** 11/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| 1 `{"temperature_c": 60, "vibration_mm_s": 2, "runtime_hours": 5000}` | champ manquant (`load_pct`) | 422 | 422 (`"type":"missing"`) |
| 2 `{..., "load_pct": 250}` | valeur absurde | 422 | 422 (`"less_than_equal"`) |
| 3 `{..., "temperature_c": "chaud"}` | texte au lieu d'un nombre | 422 | 422 (`"float_parsing"`) |
| 4 `{..., "pression_bar": 3}` | champ en trop | 422 | 422 (`"extra_forbidden"`) |
| 5 `POST /v1/predicte` | mauvaise route | 404 | 404 (`{"detail":"Not Found"}`) |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

Non, les cinq étaient justes. Le cas le moins évident est le **champ en trop**. Par défaut, Pydantic **ignore** les champs inconnus et la requête aurait reçu un 200. C'est `extra="forbid"` dans `SensorReading` qui la fait refuser en 422. Autre piège qu'on a vérifié : `"temperature_c": "72"` (un nombre écrit comme du texte) est **accepté**, car Pydantic convertit une chaîne numérique en float en mode non strict. Seul un texte non numérique comme `"chaud"` est refusé.

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
18 passed, 1 warning in 1.44s
```

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

`parametrize` exécute **la même fonction de test une fois par ligne** de la liste `CAS_REFUSES`, en injectant chaque fois les valeurs `description, url, corps, attendu`. On écrit la logique une fois et on ajoute un cas en ajoutant une ligne. pytest compte **5 tests** pour cette seule fonction (un par cas), chacun nommé dans le rapport (`test_requete_refusee[champ manquant-...]`). Si un cas échoue, on sait lequel.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
UP017 [*] Use `datetime.UTC` alias
  --> maintai\train.py:58:36
   |
58 |         "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
   |                                    ^^^^^^^^^^^^
Found 1 error.
[*] 1 fixable with `--fix`.
```

Après `ruff check . --fix` et `ruff format .` (10 fichiers reformatés), puis `python -m pytest`, qui donne toujours 18 passed :

```
All checks passed!
```

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

`ruff` fait une **analyse statique** : il lit le code **sans l'exécuter** et signale ce qui est mal écrit (imports inutiles F401, imports mal rangés I001, variables jamais utilisées, syntaxe obsolète comme UP017). Il vérifie la **forme**. `pytest`, lui, **exécute** le code et vérifie qu'il **fait ce qui est attendu** (200 pour un relevé normal, 422 pour 500 °C) : il vérifie le **comportement**. Un code peut passer ruff et être faux, ou être juste et mal écrit. Il faut les deux.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
FAILED tests/test_security.py::test_missing_key_is_rejected - AssertionError: assert 200 == 401
FAILED tests/test_security.py::test_wrong_key_is_rejected - assert 200 == 401
2 failed, 16 passed, 1 warning in 1.91s
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

`test_missing_key_is_rejected` (aucune clé) et `test_wrong_key_is_rejected` (clé `"wrong"`). Ils reçoivent **200** avec une prédiction : la route `/v1/predict` n'est pas encore protégée, et l'API répond à tout le monde.

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    expected = get_settings().api_key
    if expected is None:
        # Erreur de configuration du serveur, pas du client : 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MAINTAI_API_KEY n'est pas configurée sur le serveur",
        )
    # compare_digest : durée constante, ne trahit pas combien de caractères sont justes
    if x_api_key is None or not secrets.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Clé API absente ou invalide"
        )
```

(Les `.encode()` permettent à `compare_digest` d'accepter une clé avec des accents : sur des `str`, il n'accepte que l'ASCII.)

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

Toujours **2** (`2 failed, 16 passed`), les mêmes. La fonction existe mais **personne ne l'appelle** : tant qu'elle n'est pas déclarée comme dépendance du router, FastAPI ne l'exécute jamais, et `/v1/predict` reste ouvert.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
18 passed, 1 warning in 1.62s
```

Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl.exe`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-11-11T19:00:15Z"}` |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

Parce que les contrôles se font **dans un ordre**, et le premier qui échoue donne la réponse. La dépendance du router (`require_api_key`) est vérifiée **avant** la validation du corps. Sans clé, la requête est arrêtée au 401 et le corps n'est même pas examiné. Avec la bonne clé, elle passe l'authentification et c'est la validation Pydantic qui la refuse (422). On ne dit rien du format attendu à quelqu'un qui n'est pas authentifié.

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

**500** : `{"detail":"MAINTAI_API_KEY n'est pas configurée sur le serveur"}`. Sans `.env`, `get_settings().api_key` vaut `None` : le serveur n'a **aucune clé** à laquelle comparer. Ce n'est pas la faute du client, dont la clé est peut-être correcte (ce n'est donc pas un 401). C'est une **erreur de configuration du serveur**, donc un 5xx. Cela évite aussi le piège inverse : un serveur mal configuré qui accepterait tout le monde.

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
document.getElementById("go").addEventListener("click", async () => {
  const reading = Object.fromEntries(FEATURES.map(f => [f, Number(document.getElementById(f).value)]));
  const adresse = `${document.getElementById("url").value}/v1/predict`;
  const cle = document.getElementById("key").value;
  try {
    const resp = await fetch(adresse, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": cle },
      body: JSON.stringify(reading),            // l'objet devient du texte JSON
    });
    const data = await resp.json();             // la réponse, en objet
    if (!resp.ok) {                             // 401, 422, 503 : on affiche le code et le message
      show("err", `Erreur ${resp.status} : ${JSON.stringify(data.detail)}`);
      return;
    }
    const pct = (data.failure_probability * 100).toFixed(0);
    show(data.alert ? "alert" : "ok",
         `Probabilité de panne : ${pct} % (${data.alert ? "ALERTE" : "normal"}, seuil ${data.threshold})`);
  } catch (e) {                                 // API arrêtée, ou CORS qui bloque
    show("err", "API injoignable (serveur arrêté ou origine refusée par CORS) : " + e.message);
  }
});
```

Ce qu'affiche la page (servie sur le port 5500, `python -m http.server 5500 -d web`), observé dans Microsoft Edge (captures dans `captures/`) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | Encadré rouge : `Probabilité de panne : 95 % (ALERTE, seuil 0.3)` (valeurs par défaut 72 / 6 / 85 / 15000) |
| 500 °C, bonne clé | Encadré orange : `Erreur 422 : [{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150}}]` |
| relevé normal, fausse clé | Encadré orange : `Erreur 401 : "Clé API absente ou invalide"` |

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

Observé dans Microsoft Edge (capture `captures/web_5501_cors_5501.png`). La page affiche : `API injoignable (serveur arrêté ou origine refusée par CORS) : Failed to fetch`. La console (F12) affiche : `Access to fetch at 'http://localhost:8000/v1/predict' from origin 'http://localhost:5501' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: No 'Access-Control-Allow-Origin' header is present on the requested resource.`

Suivi de `Failed to load resource: net::ERR_FAILED`. Vérifié aussi côté serveur en reproduisant la requête préliminaire (`OPTIONS`) du navigateur. L'origine 5500 reçoit `200 OK` avec `access-control-allow-origin: http://localhost:5500`. L'origine 5501 reçoit **`400 Bad Request` sans en-tête `access-control-allow-origin`**, et le navigateur bloque donc le `POST`.

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

Parce que **CORS est appliqué par le navigateur, pas par le serveur**. Le navigateur protège l'utilisateur : il refuse qu'une page d'une origine lise les réponses d'une autre origine sans permission. `curl.exe` n'est pas un navigateur. Il n'envoie pas de requête préliminaire et ne vérifie pas `Access-Control-Allow-Origin`. Même avec un en-tête `Origin: http://localhost:5501`, notre `POST` par curl a reçu **200** et la prédiction. CORS ne remplace donc pas la clé API : seule la clé protège vraiment l'API.

**D'autres clients : le programme Java** (`java/MaintaiClient.java`, JDK 11+, sans bibliothèque externe). Même contrat que la page : `POST /v1/predict`, JSON, en-tête `X-API-Key` lu dans la variable `MAINTAI_API_KEY`.

```
javac MaintaiClient.java
set MAINTAI_API_KEY=<la clé de .env>
java MaintaiClient 72 6 85 15000          ->  Probabilité de panne : 95 % (ALERTE, seuil 0.3)
java MaintaiClient 500 6 85 15000         ->  Erreur 422 : {"detail":[{"type":"less_than_equal",...}]}
(fausse clé ou sans clé)                  ->  Erreur 401 : {"detail":"Clé API absente ou invalide"}
java MaintaiClient --file releve.json     ->  Probabilité de panne : 0 % (normal, seuil 0.3)   (relevé 60 / 2 / 50 / 5000)
(uvicorn arrêté)                          ->  API injoignable (http://localhost:8000) : uvicorn est-il lancé ?
```

Piège rencontré : le `HttpClient` de Java tente par défaut une mise à niveau HTTP/2 en clair (h2c) ; uvicorn répondait `400 Invalid HTTP request received` (ou perdait le corps : 422 `body` manquant). Correction : `.version(HttpClient.Version.HTTP_1_1)`. Le programme Java, comme curl, n'est pas soumis à CORS : il appelle l'API depuis n'importe où, seule la clé compte.

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

**4 échouent** (`4 failed, 19 passed`) : les quatre cas qui attendaient 422 reçoivent **401**, car la clé est vérifiée avant les données. Le cas **« mauvaise route »** passe quand même : `/v1/predicte` n'existe pas, le routage échoue avant toute dépendance et répond **404**, puisque la clé n'est exigée que sur les routes existantes du router `/v1`.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
23 passed, 1 warning in 1.65s
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   **401 Unauthorized** : on ne sait pas **qui** appelle (clé absente ou fausse). **422 Unprocessable Entity** : on sait qui appelle, mais les **données** envoyées sont invalides (500 °C, champ manquant). **403 Forbidden** : on sait qui appelle, la clé est valide, mais cet appelant **n'a pas le droit** de faire cette action (autorisation et non authentification ; par exemple, une clé en lecture seule qui tenterait de réentraîner le modèle).
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   Tout ce qui est dans le code finit sur GitHub, et tout ce qui est commité reste **pour toujours dans l'historique**, même si on supprime le fichier ensuite. Toute personne qui a accès au dépôt aurait la clé. `.env` contient la **vraie** clé (`MAINTAI_API_KEY=...`) et les origines CORS. Il est dans `.gitignore` et reste sur chaque machine. `.env.example` contient les **mêmes noms de variables avec de fausses valeurs** (`changez-moi`). Lui est commité : il dit quoi configurer.
3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   Une URL est enregistrée partout : journaux du serveur et des proxys, historique et favoris du navigateur, en-tête `Referer`, captures d'écran. La clé fuirait. Les en-têtes ne sont pas journalisés par défaut et ne restent pas dans l'historique.
4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   Il compare en **temps constant**. `==` s'arrête au premier caractère différent : une clé dont les 10 premiers caractères sont justes est rejetée un peu plus lentement qu'une clé fausse dès le premier. En mesurant ces durées sur beaucoup d'essais, un attaquant peut deviner la clé caractère par caractère (attaque temporelle). `compare_digest` met le même temps quel que soit l'endroit de la différence.
5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   Une origine est le triplet **schéma + domaine + port** (`http` + `localhost` + `5500`). Il suffit qu'un seul des trois diffère pour que ce soit une autre origine. `http://localhost:5500` et `http://localhost:8000` sont donc **deux origines différentes** (port différent) : la page de 5500 qui appelle l'API sur 8000 fait une requête *cross-origin*, soumise à CORS.

## 8. Le rendu Git

- Lien de la pull request : https://github.com/Anas-7bx/maintai-g1/pull/9
- Le tag `tp2` existe sur GitHub : oui (`tp2`, sur la fusion de la PR #3)
- `git status` avant le commit : le fichier `.env` apparaissait-il ? **non** (il est dans `.gitignore`, ligne `.env`)
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  … *(à compléter par le relecteur du groupe)*

## 9. Ce qui reste flou

…
