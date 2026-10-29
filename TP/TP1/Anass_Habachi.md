# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** G1  ·  **Membres :** Anass Habachi  ·  **Date :** 28/10/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
FAILED tests/test_api.py::test_predict_returns_probability - assert 422 == 200
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - KeyError: 'al...
FAILED tests/test_api.py::test_503_when_model_missing - assert 422 == 503
3 failed, 10 passed
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

Les 4 tests qui passent déjà : `test_health`, `test_out_of_range_value_is_rejected`, `test_missing_field_is_rejected` et `test_openapi_documents_predict`.

Les deux tests qui attendent un 422 passent pour une mauvaise raison. Au départ, `SensorReading` ne déclare aucun champ, et `extra="forbid"` refuse tout champ inconnu : les quatre variables du relevé sont donc toutes « inconnues ». N'importe quel relevé, même parfaitement valide, est refusé avec 422. Le test « 500 °C » passe parce que **tout** est refusé, pas parce que la borne de température est vérifiée. On le voit d'ailleurs dans les échecs : le relevé valide reçoit aussi un 422 (`assert 422 == 200`). Un test vert ne prouve rien tant qu'on ne sait pas pourquoi il passe.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | -40 | 150 | -40 °C : moteur à l'arrêt dans un local non chauffé en hiver. 150 °C : au-delà de la limite d'isolation des bobinages (classe F = 155 °C), le moteur serait détruit. |
| `vibration_mm_s` | `float` | 0 | 100 | Une vitesse de vibration efficace est positive. La norme ISO 10816 classe une machine « dangereuse » dès environ 11 à 45 mm/s selon sa taille ; 100 mm/s laisse une marge large sans accepter une valeur absurde. |
| `load_pct` | `float` | 0 | 150 | 0 % : moteur à vide. Un moteur peut être brièvement en surcharge (démarrage, à-coup) au-dessus de 100 % de sa charge nominale ; au-delà de 150 % les protections le coupent. |
| `runtime_hours` | `float` | 0 | 200 000 | Un compteur d'heures ne peut pas être négatif. 200 000 h ≈ 23 ans de marche 24 h/24, la durée de vie d'un moteur industriel. Type `float` pour accepter 15000,5 h. |

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplemente...
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
3 failed, 10 passed
```

C'est un bon signe : le nombre d'échecs ne change pas, mais leur cause oui. Avant, les relevés valides étaient bloqués par le schéma (422). Maintenant, le schéma les accepte et la requête arrive jusqu'à `predict()`, qui lève `NotImplementedError` parce qu'elle n'est pas encore écrite. La validation fonctionne ; il ne reste que la fonction.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(
        status_code=503,
        detail="Modèle non chargé : lancez python -m maintai.train, puis redémarrez l'API.",
    )
return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

500 veut dire « bug dans le code du serveur » : le client ne peut rien en conclure. 503 veut dire « service momentanément indisponible » : le code est correct, mais une ressource nécessaire (le modèle) n'est pas prête. Le client sait qu'il peut réessayer plus tard, et l'équipe sait qu'il faut entraîner ou déployer le modèle, pas corriger un bug. Le message du `detail` dit en plus quoi faire.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Charger `model.joblib` demande de lire un fichier sur le disque et de reconstruire l'objet en mémoire : c'est lent par rapport à une prédiction, qui ne prend que quelques millisecondes. En le chargeant une fois dans `state` au démarrage (`lifespan`), chaque requête réutilise le modèle déjà en mémoire : l'API répond plus vite et supporte plus de requêtes. En plus, toutes les requêtes utilisent la même version du modèle.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
13 passed, 1 warning
```

(L'avertissement vient de la bibliothèque `starlette`, qui recommande `httpx2` pour son client de test ; il ne concerne pas notre code.)

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-28T17:47:17Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

En bas de la page, dans la section **Schemas**, en ouvrant `SensorReading` : chaque champ affiche son type (`number`), sa description et ses bornes (`>= -40`, `<= 150`, etc.). On les retrouve aussi dans la route `POST /v1/predict`, onglet **Schema** du corps de la requête, à côté de l'exemple.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un ensemble de règles pour concevoir une API web : des URL claires, les méthodes HTTP (GET, POST), des codes de statut précis, du JSON, une version dans l'adresse. FastAPI est une bibliothèque Python qui permet d'écrire une API qui respecte ces règles. REST est la norme, FastAPI l'outil (et uvicorn le programme qui la fait tourner).
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   **Valider** chaque requête avant d'appeler la fonction (422 si une valeur est hors bornes ou manquante) ; **documenter** l'API automatiquement dans `/docs` (types, bornes, descriptions, exemple) ; **donner un objet Python typé** à la fonction (`reading.temperature_c` est un `float` déjà vérifié, `reading.model_dump()` donne un dictionnaire).
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` est la machine elle-même (le serveur tourne sur notre PC) ; `8000` est le port, la « porte » sur laquelle uvicorn écoute ; `/v1/predict` est la route, un chemin défini dans le code Python (et non un dossier sur le disque), avec `/v1` la version de l'API.
4. Pourquoi `/v1` dans l'adresse ?
   Pour versionner le contrat de l'API. Si on change un jour les entrées ou les sorties, on peut publier `/v2/predict` en gardant `/v1/predict` : les clients existants (tableau de bord, application mobile) continuent de fonctionner sans être modifiés.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le module Python, c'est-à-dire le fichier `maintai/api/main.py` écrit avec des points et sans `.py`. `app` est la variable de ce fichier qui contient l'application : `app = FastAPI(...)`.

## 7. Le rendu Git

- Lien de la pull request : https://github.com/Anas-7bx/maintai-g1/pull/1
- Le tag `tp1` existe sur GitHub : oui (posé sur le commit de fusion `5b1b3cb`, voir https://github.com/Anas-7bx/maintai-g1/releases/tag/tp1)
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  Personne : la pull request a été fusionnée le 29/10/2026 sans relecture d'un coéquipier, faute de disponibilité. Avant la fusion, j'ai vérifié moi-même la branche fusionnée : `python -m pytest` donne 13 passed pour TP1 et 8 passed pour TP0, aucun conflit, et ni données, ni modèle, ni `.venv` dans les changements.

## 8. Ce qui reste flou

- **Les valeurs possibles mais jamais vues à l'entraînement.** Le schéma accepte par exemple 140 °C ou 90 mm/s, parce que ces valeurs sont physiquement possibles, alors que `sensors.csv` ne va pas aussi loin. Le modèle renvoie quand même une probabilité, mais je ne sais pas si on peut lui faire confiance dans ce cas. Comment l'API devrait-elle le signaler (un avertissement dans la réponse, un journal) ? Et comment surveiller la dérive des données en production ?
- **Mettre à jour le modèle sans couper l'API.** Le modèle est chargé une seule fois, au démarrage : après un nouvel entraînement, il faut redémarrer uvicorn. Je ne vois pas encore comment on remplace le modèle dans une vraie application sans interrompre les clients (tableau de bord, application mobile), ni comment `model_version` aide à savoir quel modèle a répondu.
- **Le seuil d'alerte de 0,3.** Il est fixé dans `model_info.json` au moment de l'entraînement. Je ne sais pas encore qui doit le choisir (l'équipe de maintenance ou l'équipe data) ni s'il devrait pouvoir changer sans réentraîner le modèle.
