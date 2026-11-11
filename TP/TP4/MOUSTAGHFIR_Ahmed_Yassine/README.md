# MaintAI — TP4

Le même projet, installé comme un package. La commande `maintai-predict` interroge le modèle sans passer par l'API.

## Installation

Depuis ce dossier (`TP/TP4/MOUSTAGHFIR_Ahmed_Yassine`), dans son propre environnement :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m maintai.dataset
python -m maintai.train
pip install -e .
python -m pytest
maintai-predict 72 6 85 15000
```

Avant `pip install -e .`, pytest donne 2 failed, 25 passed. Après, 27 passed.

## Wheel

```bash
python -m build
pip install dist/maintai-0.2.0-py3-none-any.whl
```

Le wheel ne contient ni le modèle, ni les tests, ni `ui/`. Il faut livrer `models/` à côté, et installer `scikit-learn` à la version de `requirements.txt` (`MAINTAI_MODELS_DIR` pointe vers le dossier du modèle).

`dist/`, `build/` et `*.egg-info/` ne vont pas dans Git : le wheel se reconstruit.
