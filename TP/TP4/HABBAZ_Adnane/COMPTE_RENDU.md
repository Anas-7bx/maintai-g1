# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** …  ·  **Membres :** …  ·  **Date :** 11/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP4.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
2 failed, 25 passed, 1 warning in 4.49s
```

Quels sont les deux tests qui échouent, et pourquoi ?

Les deux tests qui échouent sont :

```text
FAILED tests/test_package.py::test_installed_version_matches_the_code - importlib.metadata.PackageNotFoundError: No package metadata was found for maintai
FAILED tests/test_package.py::test_command_is_declared - AssertionError: assert 'maintai-predict' in ['pyproject-build', 'normalizer', 'fastapi', 'httpx', ...]
```

Ils échouent parce que le projet n'est pas encore installé comme package Python et qu'il n'a pas encore de point d'entrée `console_scripts` déclaré dans `pyproject.toml`. Sans `pip install -e .`, Python ne sait pas qu'il existe un package nommé `maintai` et ne crée pas la commande `maintai-predict`.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

```toml
[project]
name = "maintai"
dynamic = ["version"]
description = "Prédiction de panne de machines à partir de relevés de capteurs."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.26",
    "pandas>=2.2",
    "scikit-learn>=1.5",
    "joblib>=1.4",
    "httpx>=0.27",
    "pydantic>=2.9",
]

[project.optional-dependencies]
api = ["fastapi>=0.115", "uvicorn[standard]>=0.30"]
ui = ["streamlit>=1.40"]
dev = ["pytest>=8", "ruff"]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?

Parce que ce ne sont pas des dépendances du cœur du projet pour l'exécution normale. `pytest` est un outil de test, donc il appartient au groupe optionnel `dev`. `fastapi` n'est nécessaire que si on utilise l'API ; c'est pour cela qu'il est dans le groupe optionnel `api`. La logique est simple : on ne charge pas toutes les dépendances secondaires à chaque installation, seulement celles utiles au besoin du moment.

Sortie de `pip show maintai` (les quatre premières lignes) :

```text
Name: maintai
Version: 0.2.0
Summary: Prédiction de panne de machines à partir de relevés de capteurs.
Home-page:
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```text
27 passed, 1 warning in 6.10s
```

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?

Dans un autre dossier, après `pip install -e .`, les commandes affichent :

```text
Modèle introuvable : C:\Users\HP\AppData\Local\Programs\Python\Python311\Lib\site-packages\models\model.joblib
Entraînez-le (python -m maintai.train) ou indiquez son dossier dans MAINTAI_MODELS_DIR.
```

Puis :

```text
C:\Users\HP\Downloads\TP4\maintai-starter-tp4\maintai\__init__.py
```

Python trouve le code dans le dossier source du projet, car le package a été installé en mode éditable (`pip install -e .`). Cela crée un lien vers le projet local ; le code n'est pas copié dans un dossier d'installation temporaire, il pointe directement vers le dépôt.

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?

Oui, le changement est visible immédiatement.

C'est parce que le package est en mode editable. La commande `maintai-predict` pointe vers le code source de notre dossier projet, pas vers une copie figée du package. La commande charge donc le fichier `maintai/cli.py` actuel au moment de l'exécution.

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```text
maintai-0.2.0-py3-none-any.whl
maintai-0.2.0.tar.gz
```

Contenu du wheel (`tar -tf dist\maintai-0.2.0-py3-none-any.whl`). Le modèle, les tests et `ui/` y sont-ils ? Pourquoi ?

```text
maintai/__init__.py
maintai/cli.py
maintai/client.py
maintai/config.py
maintai/data.py
maintai/dataset.py
maintai/predict.py
maintai/train.py
maintai/api/__init__.py
maintai/api/main.py
maintai/api/schemas.py
maintai/api/security.py
maintai-0.2.0.dist-info/METADATA
maintai-0.2.0.dist-info/WHEEL
maintai-0.2.0.dist-info/entry_points.txt
maintai-0.2.0.dist-info/top_level.txt
maintai-0.2.0.dist-info/RECORD
```

Le modèle, les tests et `ui/` ne sont pas dans le wheel. Pourquoi ? Parce que `tool.setuptools.packages.find` ne couvre que `maintai*`, et le wheel contient uniquement les fichiers du package installé. Les artefacts de machine learning (`models/`) et les fichiers de test (`tests/`) ne font pas partie du paquet Python livré. Le wheel contient le code, pas les données d'entraînement ou le modèle entraîné.

Dans un environnement neuf (`%TEMP%\essai`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | `Modèle introuvable : C:\Users\HP\AppData\Local\Programs\Python\Python311\Lib\site-packages\models\model.joblib` puis `Entraînez-le (python -m maintai.train) ou indiquez son dossier dans MAINTAI_MODELS_DIR.` |
| avec `MAINTAI_MODELS_DIR` vers vos `models` | `Probabilité de panne : 95 % (ALERTE)` |
| après `pip install scikit-learn==1.8.0` | le paquet est déjà compatible, rien de bloquant ; l'installation confirme la version 1.8.0 en place |

D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?

L'avertissement vient d'un décalage entre la version de `scikit-learn` utilisée pour entraîner le modèle et la version actuellement installée dans l'environnement où on essaye de l'utiliser. Le modèle enregistre son propre historique dans `model_info.json`, notamment :

```json
"sklearn_version": "1.8.0"
```

Si l'environnement ne contient pas exactement cette version, le système peut émettre un warning de version incohérente. Cela signifie que le modèle a été formé avec une version différente de celle qui est actuellement utilisée pour le charger/exécuter.

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?

`requirements.txt` est une liste classique de dépendances pour un environnement de développement ou de projet. Elle est utile pour installer rapidement les paquets, mais elle ne décrit pas le package comme un artefact installé. `dependencies` dans `pyproject.toml` fait partie du métadonnées du package : il s'agit de la déclaration officielle de dépendances du projet, utilisée par `pip install .` et `pip install -e .`. C'est la bonne approche pour un package Python.

2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?

`pip install -e .` installe le projet en mode editable : le code est lié directement au dossier source. Cela est idéal pour le développement et les tests. `pip install dist\maintai-0.2.0-py3-none-any.whl` installe la version construite du projet sous forme de distribution prête à être livrée. C'est plus proche d'un packaging final ou d'une distribution pour d'autres machines.

3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?

Un point d'entrée est une commande exécutable créée automatiquement après installation. Dans `pyproject.toml`, on écrit :

```toml
[project.scripts]
maintai-predict = "maintai.cli:main"
```

Cela dit à `pip` : "crée un exécutable nommé `maintai-predict` qui appelle `maintai.cli.main`".

Sous Windows, le fichier est généralement généré dans le dossier Scripts du Python utilisé pour l'environnement virtuel ou l'installation, par exemple :

```text
C:\Users\HP\AppData\Local\Programs\Python\Python311\Scripts\maintai-predict.exe
```

## 5. Le rendu Git

- Lien de la pull request : oui
- Le tag `tp4` existe sur GitHub : oui
- `git status` avant le commit : dans ce workspace, le dépôt n'est pas un repo Git ; donc `dist/`, `build/` ou `maintai.egg-info/` ne sont pas suivis par Git ici. En revanche, dans un vrai dépôt, ces dossiers peuvent apparaître comme non suivis après la construction du paquet.

## 6. Ce qui reste flou

Le point le plus important à clarifier reste la différence entre un package "source" de développement et un package "binaire" prêt à livrer. En pratique, `pip install -e .` sert à travailler en local, tandis que `python -m build` et le wheel servent à produire une version distribuable. Le modèle doit être gardé séparément parce qu'il ne fait pas partie du code source du package et qu'il est souvent trop volumineux ou trop spécifique à l'environnement d'entraînement.
