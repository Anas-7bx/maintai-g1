# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** G1  ·  **Membres :** Moad Bakouch  ·  **Date :** 11/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
FAILED tests/test_api.py::test_predict_returns_probability - assert 422 == 200
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - KeyError: 'alert'
FAILED tests/test_api.py::test_503_when_model_missing - assert 422 == 503
3 failed, 10 passed, 1 warning in 1.60s
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

Les 4 tests qui passent : `test_health`, `test_openapi_documents_predict`, `test_out_of_range_value_is_rejected` et `test_missing_field_is_rejected`.

Les deux tests qui attendent un 422 passent pour une mauvaise raison. Le schéma `SensorReading` ne déclare encore **aucun champ** et il a `extra="forbid"`. Tout champ envoyé est donc un « champ inconnu », et **tout relevé est refusé avec 422, même un relevé parfaitement valide** (d'où le `assert 422 == 200` du premier test qui échoue). Le 422 de la température à 500 °C ne vient pas d'une borne `le=150`, qui n'existe pas encore : il vient de `extra_forbidden`. Un test vert ne prouve rien tant qu'on ne sait pas pourquoi il passe.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | −40 | 150 | Moteur froid à l'arrêt (hiver, entrepôt non chauffé) ; au-delà de 150 °C la carcasse a dépassé la limite de l'isolation des bobinages, donc c'est une erreur de capteur. |
| `vibration_mm_s` | `float` | 0 | 50 | Une vitesse efficace n'est jamais négative ; l'ISO 10816 classe déjà « dommages » au-delà d'environ 11 mm/s, et 50 laisse de la marge pour une machine qui casse. |
| `load_pct` | `float` | 0 | 120 | 0 % à vide ; une surcharge brève jusqu'à ~120 % est possible (facteur de service 1,15 à 1,2), et c'est justement un cas à risque à ne pas refuser. |
| `runtime_hours` | `float` | 0 | 200 000 | Un compteur n'est jamais négatif ; 200 000 h, c'est environ 23 ans en 24 h/24, la durée de vie maximale d'une machine. `float`, car 15 000,5 h est légitime. |

Justification détaillée : `002-validation.md` (dans ce dossier).

> Note : le code commun du groupe (`TP/TP1/maintai/api/schemas.py`) garde des bornes plus larges (`vibration_mm_s` ≤ 100, `load_pct` ≤ 150). Les deux choix passent les 13 tests et `tests/test_casser.py` (18 passed). Je propose 50 mm/s et 120 % pour les raisons ci-dessus (ISO 10816, facteur de service) ; à trancher en groupe dans l'ADR 002.

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplementedError
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
maintai\api\main.py:46: NotImplementedError
3 failed, 10 passed, 1 warning in 2.46s
```

C'est un bon signe. Toujours 3 échecs, mais l'erreur n'est plus un 422 : c'est `NotImplementedError`, levée dans `predict()`. Le schéma **accepte** maintenant les relevés valides, la requête franchit la validation et arrive jusqu'à la fonction. Il ne reste plus qu'à écrire son corps. Et le test du 500 °C passe désormais pour la bonne raison : la borne `le=150`.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé : lancez python -m maintai.train puis redémarrez l'API",
        )
    return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

500 veut dire « bug dans le code du serveur », une erreur inattendue. Ici, rien n'est cassé : la situation est prévue, et le service est **temporairement indisponible** tant qu'un modèle n'a pas été entraîné et chargé. 503 Service Unavailable dit exactement cela au client : « ce n'est pas ta faute (pas un 4xx), réessaie plus tard ». Notre message dit en plus quoi faire. Sans le `if`, `None.predict(...)` lèverait un `AttributeError` et le client recevrait un 500 sans explication.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Lire `model.joblib` et `model_info.json` sur le disque et désérialiser le pipeline prend du temps : plusieurs millisecondes, voire des secondes pour un gros modèle. C'est bien plus long que la prédiction elle-même. Le charger à chaque requête ralentirait chaque réponse et multiplierait les lectures disque. Chargé une fois dans `lifespan` et gardé dans `state`, il sert toutes les requêtes, et tous les clients utilisent la même version. On sait aussi dès le démarrage, via `/health`, si le modèle manque.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
13 passed, 1 warning in 1.41s
```

(Avec `tests/test_casser.py` de la séance 5 : `18 passed, 1 warning in 1.44s`. L'avertissement est une `StarletteDeprecationWarning` interne à `fastapi.testclient`, sans lien avec notre code.)

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-11-11T18:53:22Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans la section **Schemas** en bas de la page, sous `SensorReading`. Chaque champ y affiche son type (`number`), sa description et ses bornes (`minimum: -40`, `maximum: 150`, etc.). On les voit aussi dans l'onglet **Schema** du corps de requête de `POST /v1/predict`, à côté de l'exemple. Elles viennent toutes de `Field(ge=..., le=...)`.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un **ensemble de règles** pour concevoir une API web : des URL claires qui désignent des ressources (`/health`, `/v1/predict`), les méthodes HTTP (GET lit, POST envoie), des codes de statut précis, du JSON et une version dans l'URL. FastAPI est une **bibliothèque Python** qui permet d'écrire une API qui suit ces règles. On pourrait écrire une API REST avec Flask, Express ou Spring, et une API non REST avec FastAPI.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   (1) **Valider** chaque requête avant d'appeler la fonction (422 en indiquant où et pourquoi) ; (2) **documenter** l'API (`/docs` généré automatiquement, avec types, bornes, descriptions et exemple) ; (3) **donner un objet Python typé** à la fonction (`reading.temperature_c` est un `float` déjà vérifié, et `model_dump()` en fait un dictionnaire). Les trois viennent de la même source et ne peuvent donc pas se contredire.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` désigne la machine elle-même (le serveur tourne sur notre PC). `8000` est le port, la « porte » sur laquelle uvicorn écoute. `/v1/predict` est la route, un chemin défini dans le code Python (pas un dossier sur le disque), dont `/v1` est la version de l'API.
4. Pourquoi `/v1` dans l'adresse ?
   Pour versionner le **contrat** de l'API. Si un jour on change les champs d'entrée ou de sortie (une nouvelle variable, par exemple), on publie `/v2` à côté de `/v1`. Les clients existants continuent de marcher pendant qu'ils migrent. Sans version, chaque changement casserait tous les clients d'un coup.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le module Python à importer, c'est-à-dire le fichier `maintai/api/main.py` écrit avec des points. `app` est la **variable** de ce module qui contient l'application (`app = FastAPI(...)`), celle qu'uvicorn fait tourner.

## 7. Le rendu Git

- Lien de la pull request : https://github.com/Anas-7bx/maintai-g1/pull/8
- Le tag `tp1` existe sur GitHub : oui (tag de groupe `tp1`, posé après la fusion de la PR #1)
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  … *(à compléter par le relecteur du groupe)*

## 8. Ce qui reste flou

…
