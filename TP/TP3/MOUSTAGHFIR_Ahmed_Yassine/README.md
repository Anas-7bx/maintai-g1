# MaintAI — TP3

Interface Streamlit pour voir les relevés et demander une prédiction à l'API du TP2.

## Installation

Depuis ce dossier (`TP/TP3/MOUSTAGHFIR_Ahmed_Yassine`) :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m maintai.dataset
python -m maintai.train
cp .env.example .env
python -m pytest
```

`python -m pytest` doit afficher 23 passed.

## Lancer

Terminal 1 :

```bash
uvicorn maintai.api.main:app --reload --env-file .env
```

Terminal 2 :

```bash
python -m streamlit run ui/app.py
```

La page s'ouvre sur http://localhost:8501. La clé se saisit dans la barre latérale. Le fichier `.env` ne doit pas être commité.
