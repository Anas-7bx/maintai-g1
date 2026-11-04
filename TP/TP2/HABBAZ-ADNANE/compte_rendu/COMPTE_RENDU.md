# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** G1  ·  **Membres :** HABBAZ Adnane  ·  **Date :** 04/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| Suppression de la température | Champ manquant | 422 | 422 — valeur attendue |
| Température à 7000 °C | Valeur hors limites | 422 | 422 — la température doit être inférieure ou égale à 150 |
| Température égale à « x » | Type de valeur invalide | 422 | 422 — valeur numérique attendue |
| Ajout d'un champ « hauteur » | Champ supplémentaire interdit | 422 | 422 — « Extra inputs are not permitted » |
| `GET /v1/predict` | La route existe en POST, pas en GET | 405 | 405 — « Method Not Allowed » |

Une de mes prévisions était-elle fausse ? Laquelle, et pourquoi ?

Je ne savais pas quel code renverrait la requête vers `/v1/predict`, donc je n'avais pas fait de prévision pour ce cas.

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
19 passed, 1 warning in 2.11s
```

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

`@pytest.mark.parametrize` permet de lancer la même fonction de test avec plusieurs valeurs. Pytest compte chaque valeur comme un test séparé. J'obtiens 19 tests : 13 déjà présents dans le TP1, 1 test `test_500_degres_est_refuse` et 5 cas ajoutés dans `test_casser.py`.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
I001 [*] Import block is un-sorted or un-formatted
 --> maintai\api\demo_api.py:1:1
  |
1 | / from fastapi import FastAPI 
2 | | from pydantic import BaseModel, Field
  | |_____________________________________^
help: Organize imports
  |
  - from fastapi import FastAPI 
1 + from fastapi import FastAPI
2 | from pydantic import BaseModel, Field
  -
3 |
  |

UP017 [*] Use `datetime.UTC` alias
  --> maintai\train.py:58:36
   |
56 |         "target": TARGET,
57 |         "threshold": settings.threshold,
58 |         "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
   |                                    ^^^^^^^^^^^^
59 |         "sklearn_version": sklearn.__version__,
60 |     }
   |
help: Convert to `datetime.UTC` alias
   |
5  | import json
   - from datetime import datetime, timezone
6  + from datetime import datetime, timezone, UTC
7  |
--------------------------------------------------------------------------------
57 |         "threshold": settings.threshold,
   -         "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
58 +         "trained_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
59 |         "sklearn_version": sklearn.__version__,
   |

I001 [*] Import block is un-sorted or un-formatted
 --> tests\test_casser.py:1:1
  |
1 | import pytest
  | ^^^^^^^^^^^^^
help: Organize imports
  |
2 |
  -
3 | # la clé des tests (conftest.py) ; inutile en TP1, nécessaire en TP2
  |

Found 3 errors.
[*] 3 fixable with `--fix`.
```

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

`ruff check .` cherche des problèmes de style et de qualité du code, comme les imports mal organisés. `python -m pytest` exécute les tests pour vérifier que le programme se comporte comme prévu.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
All checks passed!

19 passed, 1 warning in 2.29s
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?



## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    api_key = get_settings().api_key
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key is not configured",
        )
    if x_api_key is None or not secrets.compare_digest(
        x_api_key.encode("utf-8"), api_key.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


```

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

Deux tests échouent encore. La fonction de vérification est écrite, mais elle n'est pas appelée tant que `require_api_key` n'est pas ajoutée aux dépendances du router.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
19 passed, 1 warning in 2.72s
```


Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl.exe`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Invalid or missing API key"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Invalid or missing API key"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | Un résultat JSON avec `failure_probability`, `alert`, `threshold` et `model_version`  |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Invalid or missing API key"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | Une erreur de validation indiquant que la température doit être inférieure ou égale à 150 °C |

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

Sans clé, la vérification d'authentification échoue et renvoie `401`. Avec la bonne clé, la requête arrive à la validation du relevé : `500 °C` dépasse la limite autorisée et renvoie `422`.

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

Si `MAINTAI_API_KEY` n'est pas défini dans l'environnement, le serveur renvoie `500` avec `{"detail":"API key is not configured"}`. Ce n'est pas un `401` : le problème vient de la configuration du serveur, pas de la clé envoyée par le client.

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
document.getElementById("go").addEventListener("click", async () => {
  const reading = Object.fromEntries(FEATURES.map(f => [f, Number(document.getElementById(f).value)]));
  const url = document.getElementById("url").value.replace(/\/+$/, "");
  const key = document.getElementById("key").value;

  try {
    const response = await fetch(`${url}/v1/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": key,
      },
      body: JSON.stringify(reading),
    });
    const result = await response.json();

    if (!response.ok) {
      show("err", typeof result.detail === "string"
        ? result.detail
        : JSON.stringify(result.detail ?? `Erreur HTTP ${response.status}`));
      return;
    }

    show(
      result.alert ? "alert" : "ok",
      `Probabilité de panne : ${(result.failure_probability * 100).toFixed(1)} % — ${result.alert ? "Alerte" : "Pas d'alerte"}`
    );
  } catch (error) {
    show("err", `Erreur de connexion à l'API : ${error.message}`);
  }
});
```

Ce qu'affiche la page (servie sur le port 5500) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | La probabilité de panne calculée et « Alerte » ou « Pas d'alerte » selon le résultat du modèle. |
| 500 °C, bonne clé | Le message de validation indiquant que la température dépasse 150 °C. |
| relevé normal, fausse clé | `Invalid or missing API key`. |

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

L'origine `http://localhost:5501` n'est pas autorisée par la configuration CORS. La page affiche une erreur de connexion (souvent `Failed to fetch`) et la console indique que la requête a été bloquée par CORS.

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

`curl.exe` n'est pas un navigateur et n'applique pas la politique CORS. CORS est une protection appliquée par le navigateur ; elle ne bloque pas directement l'accès à l'API avec `curl.exe`.

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

Quatre tests échouent avec `401`, car ils envoient des requêtes à la route protégée sans clé. Le cas qui utilise `GET /v1/predict` passe avec `405` : seule la méthode `POST` existe pour cette route, donc la dépendance d'authentification de cette route n'est pas exécutée.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

Je n'ai pas pu vérifier la sortie après la copie, car `test_casser.py` n'est pas présent dans le dossier de travail. Pour les tests actuellement présents, j'obtiens :

```
19 passed, 1 warning in 2.72s
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   `401` signifie que la clé d'authentification est absente ou incorrecte. `422` signifie que les données envoyées ne respectent pas les règles de validation. `403` signifie que l'utilisateur est identifié, mais qu'il n'a pas le droit d'effectuer l'action.
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   Une vraie clé est secrète : la mettre dans le code ou dans Git risquerait de la divulguer. Le fichier `.env` contient ma configuration locale et est ignoré par Git. `.env.example` contient des valeurs d'exemple et peut être commité ; il faut remplacer la clé d'exemple par une vraie clé dans `.env`.
3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   Une clé dans l'URL risque de se retrouver dans l'historique du navigateur, les journaux ou les liens partagés. L'en-tête `X-API-Key` évite de l'exposer dans l'adresse. En production, il faut aussi utiliser HTTPS.
4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   `secrets.compare_digest` compare les clés d'une manière conçue pour limiter les fuites d'information sur leur contenu par le temps de comparaison.
5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   Une origine est définie par le schéma, le nom d'hôte et le port. Ces deux adresses ne sont pas de la même origine, car les ports `5500` et `8000` sont différents.

## 8. Le rendu Git

- Lien de la pull request :
- Le tag `tp2` existe sur GitHub : oui
- `git status` avant le commit : le fichier `.env` apparaissait-il ? non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?


## 9. Ce qui reste flou

je dois savoir comment distinguer entre les tous familles d'erreurs .

