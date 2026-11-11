# Compte rendu · TP4 : MaintAI devient un package Python

**ANASS HABACHI  G1**   ·  **Date :** 11/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP4.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
================= 2 failed, 25 passed, 1 warning in 16.62s =================
```

Quels sont les deux tests qui échouent, et pourquoi ?

Les deux tests de `tests/test_package.py` :
- `test_installed_version_matches_the_code` : `PackageNotFoundError: No package metadata was found for maintai`. Le dossier `maintai/` existe, mais il n'est pas encore installé comme package : pip ne le connaît pas, il n'a donc pas de version.
- `test_command_is_declared` : `AssertionError: assert 'maintai-predict' in [...]`. La commande `maintai-predict` n'est déclarée nulle part, car `[project.scripts]` est encore un TODO dans `pyproject.toml`.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

```toml
dependencies = [
    "numpy>=2.0",
    "pandas>=2.2",
    "scikit-learn>=1.5",
    "joblib>=1.4",
    "httpx>=0.27",
]

[project.scripts]
maintai-predict = "maintai.cli:main"
```

Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?

`dependencies` contient seulement ce dont le code de `maintai/` a besoin pour fonctionner (prédire, charger les données, appeler l'API). `pytest` ne sert qu'aux développeurs pour tester, et `fastapi` ne sert qu'à faire tourner l'API. Un collègue qui veut seulement `maintai-predict` n'en a pas besoin. Ils sont donc dans les groupes optionnels (`dev`, `api`, `ui`), qu'on installe sur demande : `pip install -e ".[api,dev]"`.

Sortie de `pip show maintai` (les quatre premières lignes) :

```
Name: maintai
Version: 0.2.0
Summary: Prédiction de panne de machines à partir de relevés de capteurs
Home-page:
```

Les lignes suivantes montrent aussi `Editable project location: C:\Users\DELL\Downloads\maintai-starter-tp4` et `Requires: httpx, joblib, numpy, pandas, scikit-learn`.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
====================== 27 passed, 1 warning in 11.27s ======================
```

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?

```
> maintai-predict 72 6 85 15000
Probabilité de panne : 95 % (ALERTE)
> python -c "import maintai; print(maintai.__file__)"
C:\Users\DELL\Downloads\maintai-starter-tp4\maintai\__init__.py
```

La commande fonctionne depuis n'importe quel dossier. Python trouve le code de `maintai` dans le dossier du projet (`maintai-starter-tp4\maintai`), pas dans une copie placée dans `site-packages` : `pip install -e .` a posé un lien vers le dossier du projet. La commande elle-même est le fichier `.venv\Scripts\maintai-predict.exe`, créé par pip à l'installation.

Conséquence : `streamlit run ui/app.py` fonctionne maintenant sans `python -m`, alors qu'il donnait `ModuleNotFoundError` au TP3. `maintai` est trouvé grâce à l'installation, quel que soit le dossier de lancement.

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?

Oui. Après avoir remplacé « Probabilité de panne » par « Risque de panne (message modifié) », la commande affiche immédiatement :

```
Risque de panne (message modifié) : 95 % (ALERTE)
```

Le changement est visible sans réinstaller, parce qu'en mode éditable Python lit directement les fichiers du dossier du projet : il n'y a pas de copie à mettre à jour. Le message d'origine a ensuite été remis (27 tests passent toujours).

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```
maintai-0.2.0-py3-none-any.whl   11 628 octets
maintai-0.2.0.tar.gz             12 361 octets
```

`python -m build` fabrique deux fichiers : le wheel (`.whl`, prêt à installer) et l'archive des sources (`.tar.gz`).

Contenu du wheel (`tar -tf dist\maintai-0.2.0-py3-none-any.whl`). Le modèle, les tests et `ui/` y sont-ils ? Pourquoi ?

```
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

Non : ni le modèle (`models/`), ni les tests (`tests/`), ni `ui/` ne sont dans le wheel. `pyproject.toml` dit `include = ["maintai*"]` : seul le dossier `maintai/` entre dans le package. Le wheel contient le code, plus ses métadonnées (`dist-info`), dont `entry_points.txt` qui déclare la commande `maintai-predict`. Le modèle est un fichier produit par l'entraînement, il se livre à part.

Dans un environnement neuf (`%TEMP%\essai`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | `Modèle introuvable : C:\Users\DELL\AppData\Local\Temp\essai\.venv\Lib\site-packages\models\model.joblib`, puis « Entraînez-le (python -m maintai.train) ou indiquez son dossier dans MAINTAI_MODELS_DIR. » (code de sortie 1) |
| avec `MAINTAI_MODELS_DIR` vers vos `models` | `Probabilité de panne : 95 % (ALERTE)`, mais précédé de trois avertissements : `InconsistentVersionWarning: Trying to unpickle estimator StandardScaler from version 1.8.0 when using version 1.9.1` (idem pour `LogisticRegression` et `Pipeline`) |
| après `pip install scikit-learn==1.8.0` | `Probabilité de panne : 95 % (ALERTE)`, sans aucun avertissement |

Pour faire marcher la commande chez le collègue, il a fallu deux choses en plus du wheel : indiquer le dossier du modèle (`MAINTAI_MODELS_DIR`) et installer la version exacte de scikit-learn qui a écrit le modèle. Livrer un modèle, c'est donc trois choses : le code (le wheel), le modèle (`models/`) et les versions exactes.

En PowerShell, les commandes sont : `$env:MAINTAI_MODELS_DIR = "C:\Users\DELL\Downloads\maintai-starter-tp4\models"` (au lieu de `set ...` dans `cmd`), puis `pip install scikit-learn==1.8.0`.

D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?

Le wheel déclare `scikit-learn>=1.5` : dans l'environnement neuf, pip a donc installé la version la plus récente, **1.9.1**. Mais le modèle `model.joblib` a été écrit (« picklé ») avec scikit-learn **1.8.0**. En le relisant avec une autre version, scikit-learn prévient que les objets (`StandardScaler`, `LogisticRegression`, `Pipeline`) peuvent ne plus se comporter pareil, voire donner des résultats faux.

La ligne de `models/model_info.json` qui l'explique :

```json
"sklearn_version": "1.8.0"
```

C'est pour cela que `requirements.txt` fixe `scikit-learn==1.8.0` (exactement), alors que `pyproject.toml` dit seulement `>=1.5` (au moins). Un modèle se relit avec la version qui l'a écrit.

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?
   `requirements.txt` fixe des versions **exactes** (`==`) : il reproduit à l'identique l'environnement de développement, et un modèle se relit avec la version de scikit-learn qui l'a écrit. `dependencies` donne des versions **minimales** (`>=`) : un package doit pouvoir s'installer à côté d'autres packages sans leur imposer une version précise.
2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?
   `pip install -e .` (éditable) pose un lien vers le dossier du projet : les modifications du code sont visibles tout de suite. C'est pour développer. Le wheel est une copie figée du code, installée dans `site-packages` : il ne dépend plus du dossier du projet. C'est pour livrer à quelqu'un d'autre.
3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?
   C'est une commande déclarée dans `pyproject.toml`, reliée à une fonction Python (`maintai-predict = "maintai.cli:main"`). À l'installation, pip crée un petit exécutable qui appelle cette fonction, dans le dossier `Scripts` de l'environnement : `.venv\Scripts\maintai-predict.exe`. Comme ce dossier est dans le `PATH` quand le `.venv` est activé, la commande se lance depuis n'importe quel dossier.

## 5. Le rendu Git

- Lien de la pull request : https://github.com/Anas-7bx/maintai-g1/pull/12 (branche `tp4-anass`, dossier `TP/TP4/ANASS_HABACHI_TP4`)
- Le tag `tp4` existe sur GitHub : non, pas encore (il se pose après la fusion de la pull request)
- `git status` avant le commit : `dist/`, `build/` ou `maintai.egg-info/` apparaissaient-ils ? **non** : seuls `pyproject.toml` et `COMPTE_RENDU.md` ont été ajoutés au dépôt. Le wheel se reconstruit avec `python -m build`, il ne va pas dans Git.

## 6. Ce qui reste flou

**Mon avis :** ce TP m'a montré la différence entre développer et livrer. En mode éditable, tout marche tout de suite parce que le code, le modèle et les bonnes versions sont sur ma machine. Avec le wheel seul, dans un environnement neuf, on voit tout ce qui manque : livrer un modèle, c'est trois choses, le code (le wheel), le modèle (`models/`) et les versions exactes.

**Ce qui reste un peu flou pour moi :**
- Comment livrer le modèle proprement à un collègue : un dossier à copier à la main et une variable `MAINTAI_MODELS_DIR` à définir, cela reste fragile.
- Comment publier le wheel pour qu'on puisse l'installer avec un simple `pip install maintai` (sur PyPI ou un dépôt interne).

**Les difficultés que j'ai rencontrées :**
1. **Les commandes du polycopié sont pour `cmd`** : en PowerShell, `cd /d %TEMP%` devient `cd $env:TEMP`, et `set MAINTAI_MODELS_DIR=...` devient `$env:MAINTAI_MODELS_DIR = "..."`.
2. **Un `.venv` séparé pour le TP4** : il faut bien vérifier que `(.venv)` est celui du TP4 avant `pip install -e .`, sinon `maintai` s'installe dans l'environnement du TP1.
