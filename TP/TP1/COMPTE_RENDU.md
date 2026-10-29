# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** G1  **Membres :** HABBAZ ADNANE ·  **Date :** 28/10/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
3 failed, 10 passed, 1 warning in 0.82s
```


## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | `float` | -40 °C | 150 °C | Plage réaliste pour la température d'un moteur. |
| `vibration_mm_s` | `float` | 0 mm/s | 100 mm/s | Une vibration ne peut pas être négative ; 100 est une limite haute. |
| `load_pct` | `float` | 0 % | 150 % | Une charge peut dépasser la charge nominale, mais pas être négative. |
| `runtime_hours` | `float` | 0 h | 200 000 h | Le temps de fonctionnement cumulé ne peut pas être négatif. |

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```
3 failed, 10 passed, 1 warning in 0.71s
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplementedError
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError.
```

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

Parce que le service est temporairement indisponible : le modèle peut être entraîné puis chargé.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Pour éviter de le recharger à chaque appel, ce qui ralentirait les réponses.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
13 passed, 1 warning in 8.98s
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancez `uvicorn maintai.api.main:app --reload`, puis envoyez ces requêtes depuis `/docs` (ou avec `curl.exe`).

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-28T16:56:08Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans le schéma de `POST /v1/predict`

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   1- REST est un style de conception d'API ; FastAPI est un outil Python pour en créer.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   2-Valider les données, générer la documentation et décrire les entrées/sorties attendues.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   3-`localhost` est la machine locale, `8000` le port, et `/v1/predict` le chemin de l'API.
4. Pourquoi `/v1` dans l'adresse ?
   4-Pour identifier la version 1 de l'API et faciliter une évolution future.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   5-`maintai.api.main` est le module Python ; `app` est l'application FastAPI qu'il contient.

## 7. Le rendu Git

- Lien de la pull request : https://github.com/Anas-7bx/maintai-g1/pull/1
- Le tag `tp1` existe sur GitHub : oui / non
   oui
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
Aucune revue n’a été laissée sur la pull request 1 du dépôt

## 8. Ce qui reste flou

Aucun point flou pour le moment.
