# Compte rendu · TP4 : MaintAI devient un package

**Groupe :** G1  ·  **Membres :** MOUSTAGHFIR Ahmed Yassine  ·  **Date :** 11/11/2026

## 1. Avant l'installation

`pip install -r requirements.txt`, puis `python -m pytest`, sans `pip install -e .` :

```text
2 failed, 25 passed, 1 warning in 1.80s
```

Les deux échecs sont dans `tests/test_package.py`. `version("maintai")` lève `PackageNotFoundError`. La commande `maintai-predict` n'est pas dans les scripts installés.

## 2. Installation éditable

`pyproject.toml` déclare les bibliothèques importées par le package (`pandas`, `numpy`, `scikit-learn`, `joblib`, `httpx`) et la commande :

```toml
[project.scripts]
maintai-predict = "maintai.cli:main"
```

`pytest`, `ruff`, `fastapi` et `streamlit` restent dans les groupes `dev`, `api` et `ui`.

```text
$ pip show maintai
Name: maintai
Version: 0.2.0
Editable project location: TP/TP4/MOUSTAGHFIR_Ahmed_Yassine
```

```text
$ maintai-predict 72 6 85 15000
Probabilité de panne : 95 % (ALERTE)
```

Le modèle vient de `python -m maintai.train` sur 5 000 relevés : accuracy 0,904, recall 0,75, precision 0,622, seuil 0,3. La probabilité brute est 0,9475, donc 95 % après `round`.

```text
27 passed, 1 warning in 1.72s
```

Depuis `/tmp`, la même commande affiche encore « Probabilité de panne : 95 % (ALERTE) ». `maintai.__file__` pointe vers `TP/TP4/MOUSTAGHFIR_Ahmed_Yassine/maintai/__init__.py` : `pip install -e .` pose un lien, pas une copie.

J'ai changé le texte de `maintai/cli.py` en « Probabilité de panne (essai) ». La commande a affiché le nouveau texte sans réinstaller. J'ai remis la phrase d'origine.

`streamlit run ui/app.py` trouve `maintai` grâce à ce lien. En TP3, sans installation, il fallait `python -m streamlit run` depuis le dossier du projet pour que Python voie le paquet.

## 3. Le wheel

`python -m build` produit `dist/maintai-0.2.0-py3-none-any.whl`. Dedans : le paquet `maintai` (y compris `cli.py` et `api/`) et les métadonnées. Pas de `models/`, pas de `tests/`, pas de `ui/`.

Dans un environnement neuf, avec seulement le wheel :

| Essai | Message obtenu |
|---|---|
| premier lancement | Modèle introuvable |
| `MAINTAI_MODELS_DIR` vers `models/` | `InconsistentVersionWarning` : StandardScaler, LogisticRegression et Pipeline écrits avec scikit-learn 1.8.0, relus avec 1.9.1. Puis « Probabilité de panne : 95 % (ALERTE) » |
| `pip install scikit-learn==1.8.0`, même variable | Probabilité de panne : 95 % (ALERTE), sans l'avertissement |

La ligne de `models/model_info.json` qui explique l'avertissement est `"sklearn_version": "1.8.0"`. Le wheel dit « au moins » (`scikit-learn>=1.5`) : pip a pris 1.9.1. `requirements.txt` dit « exactement » (`scikit-learn==1.8.0`), la version qui a écrit le modèle.

Livrer une prédiction, c'est trois choses : le code (le wheel), le modèle (`models/`) et les versions exactes.

## 4. Rendu Git

Pas de pull request, pas de tag `tp4`. `dist/`, `build/` et `maintai.egg-info/` sont dans `.gitignore`. Le dossier est prêt à être poussé, il n'a pas été poussé.

Chemin prévu : `TP/TP4/MOUSTAGHFIR_Ahmed_Yassine/`.

## 5. Ce qui reste flou

Je comprends qu'une installation éditable sert à développer et que le wheel sert à livrer. Je suis moins sûr de la façon de versionner le modèle quand le code passe de 0.2.0 à 0.3.0 sans réentraîner.
