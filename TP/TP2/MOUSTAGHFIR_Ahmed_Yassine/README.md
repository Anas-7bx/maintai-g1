# MaintAI — TP2

Prédiction de panne, protégée par une clé d'API. Une page servie sur le port 5500 appelle `/v1/predict`.

## Installation

Depuis ce dossier (`TP/TP2/MOUSTAGHFIR_Ahmed_Yassine`) :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Données, entraînement, tests

```bash
python -m maintai.dataset
python -m maintai.train
python -m pytest
```

`python -m pytest` doit afficher 23 passed.

## Lancer l'API et la page

```bash
cp .env.example .env
# remplacez changez-moi par votre clé
uvicorn maintai.api.main:app --reload --env-file .env
```

Dans un second terminal, même dossier :

```bash
python -m http.server 5500 -d web
```

Ouvrez http://localhost:5500 et saisissez la clé de `.env`. Le fichier `.env` ne doit pas être commité.
