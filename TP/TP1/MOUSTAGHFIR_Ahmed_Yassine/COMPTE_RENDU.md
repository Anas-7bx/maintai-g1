# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** G1  ·  **Membres :** MOUSTAGHFIR Ahmed Yassine  ·  **Date :** 28/10/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
3 failed, 10 passed, 1 warning in 0.86s
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

Les quatre qui passent : `test_health`, `test_out_of_range_value_is_rejected`, `test_missing_field_is_rejected`, `test_openapi_documents_predict`. Les trois qui échouent : `test_predict_returns_probability` (422 au lieu de 200), `test_high_risk_reading_raises_alert`, `test_503_when_model_missing` (422 au lieu de 503).

Les deux tests 422 passent pour une mauvaise raison. `SensorReading` n'a encore aucun champ, et `extra="forbid"` refuse tout champ inconnu. `temperature_c`, `vibration_mm_s`, `load_pct` et `runtime_hours` sont donc tous refusés, même dans un relevé correct. Le 422 ne prouve pas que la borne `le=150` existe : un bon relevé est rejeté lui aussi.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | float | −40 | 150 | Plage d'un capteur d'atelier. 150 °C est déjà au-delà d'un moteur en service. Le fichier synthétique est bien plus étroit. |
| `vibration_mm_s` | float | 0 | 50 | Une vitesse de vibration ne peut pas être négative. 50 mm/s est un niveau destructeur, plus large que le maximum du CSV. |
| `load_pct` | float | 0 | 150 | 0 % : machine à vide. Une surcharge peut dépasser 100 % de la charge nominale ; 150 % est une limite de protection. |
| `runtime_hours` | float | 0 | 100 000 | Le compteur part de zéro et peut dépasser 20 000 h. Le type `float` accepte 15 000,5 h. |

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```
3 failed, 10 passed, 1 warning in 0.77s
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplementedError
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
```

C'est un bon signe : le relevé valide n'est plus rejeté en 422. Il traverse le schéma et arrive dans `predict()`, qui lève encore `NotImplementedError`.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
predictor = state.get("predictor")
if predictor is None:
    raise HTTPException(
        status_code=503,
        detail="Modèle non chargé. Lancez python -m maintai.train, puis redémarrez l'API.",
    )
return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

Le 500 veut dire un bug dans le code. Ici le service tourne, mais le fichier du modèle n'est pas là : c'est un service indisponible. Le 503 le dit, et le message indique la commande à lancer. Un client peut réessayer après l'entraînement.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

`joblib.load` lit le disque et reconstruit le pipeline. Le faire à chaque relevé ralentirait l'API et relirait le même fichier. `lifespan` le charge dans `state` au démarrage. Chaque requête ne fait plus que `predict`.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
13 passed, 1 warning in 0.78s
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-28T17:17:01Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans le schéma `SensorReading` de `POST /v1/predict` : chaque champ affiche son type, sa description, et les bornes `minimum` / `maximum` (par exemple température de −40 à 150). L'exemple du schéma est aussi affiché. Le bouton « Try it out » avec 500 °C renvoie le 422 ci-dessus.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est une façon de concevoir une API : des adresses claires, les méthodes HTTP, des codes de statut, du JSON, une version dans l'adresse. FastAPI est la bibliothèque Python avec laquelle on écrit cette API. uvicorn est le programme qui la fait écouter sur un port.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   Il valide la requête avant d'appeler la fonction (un 500 °C ne voit jamais le modèle). Il documente `/docs` (type, bornes, description, exemple). Il fournit un objet Python déjà typé : `reading.temperature_c` est un `float`, et `reading.model_dump()` donne le dictionnaire attendu par le modèle.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` est la machine elle-même. `8000` est le port où uvicorn écoute. `/v1/predict` est la route choisie dans le code, pas un dossier sur le disque.
4. Pourquoi `/v1` dans l'adresse ?
   C'est la version du contrat. On pourra changer l'API plus tard sans casser les clients qui parlent encore à `/v1`.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le module `maintai/api/main.py`, écrit avec des points. `app` est la variable `app = FastAPI()` de ce fichier.

## 7. Le rendu Git

- Lien de la pull request : non créé dans ce dépôt
- Le tag `tp1` existe sur GitHub : non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  Pas de relecture : la pull request n'a pas été ouverte.

## 8. Ce qui reste flou

Le seuil 0,3 est fixé dans la configuration. Je vois qu'il change le rappel et la précision, mais pas encore comment le choisir à partir du coût d'une panne manquée et d'une heure d'inspection.
