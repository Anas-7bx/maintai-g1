# Compte rendu · TP4 : MaintAI devient un package Python

**Groupe :** G1  ·  **Membres :** Moad Bakouch  ·  **Date :** 11/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP4.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP4`, avec son propre `.venv`)

Dernière ligne de `python -m pytest` juste après `pip install -r requirements.txt` :

```
FAILED tests/test_package.py::test_installed_version_matches_the_code - importlib.metadata.PackageNotFoundError: No package metadata was found for maintai
FAILED tests/test_package.py::test_command_is_declared - AssertionError: assert 'maintai-predict' in [...]
2 failed, 25 passed, 1 warning in 4.86s
```

Quels sont les deux tests qui échouent, et pourquoi ?

Les deux tests de `tests/test_package.py`. `test_installed_version_matches_the_code` demande à `importlib.metadata` la version **installée** de `maintai`, mais le package n'est pas installé : il n'existe aucune métadonnée (`PackageNotFoundError`). `test_command_is_declared` cherche `maintai-predict` parmi les points d'entrée `console_scripts` installés, et ne le trouve pas : `pyproject.toml` ne déclare pas encore `[project.scripts]` et rien n'est installé. Le **code** fonctionne (les 25 autres tests passent avec `pythonpath = .`), mais il n'est pas encore un **package**.

## 2. Sprint 1 : `pyproject.toml` et `pip install -e .`

Vos sections `dependencies` et `[project.scripts]` :

```toml
# Ce que le code de maintai/ importe pour fonctionner : des minimums (>=), pas des versions figées
dependencies = [
    "numpy>=1.26",        # dataset.py
    "pandas>=2.2",        # data.py, dataset.py, predict.py
    "scikit-learn>=1.5",  # data.py, train.py (et pour relire model.joblib)
    "joblib>=1.4",        # train.py, predict.py
    "httpx>=0.27",        # client.py
]

# Une commande installée dans .venv\Scripts\maintai-predict.exe, qui appelle maintai.cli.main
[project.scripts]
maintai-predict = "maintai.cli:main"
```

Pourquoi `pytest` et `fastapi` ne sont-ils pas dans `dependencies` ?

`dependencies` liste ce qu'il faut pour **utiliser** le cœur du package (prédire, `maintai-predict`, le client). Tout le monde les installe. **`pytest`** ne sert qu'aux développeurs qui lancent les tests : il est dans le groupe optionnel `dev`. **`fastapi`** (et uvicorn) ne sert qu'à qui veut faire tourner l'API : il est dans le groupe `api` (`pip install "maintai[api]"`), et `streamlit` est dans `ui`. Les mettre dans `dependencies` imposerait à un collègue qui veut seulement la commande d'installer un serveur web, une interface et un framework de test, ce qui est lourd et augmente le risque de conflits de versions.

Sortie de `pip show maintai` (les quatre premières lignes) :

```
Name: maintai
Version: 0.2.0
Summary: Prédiction de panne de machines à partir de relevés de capteurs (modèle, API, client, commande)
Home-page:
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
27 passed, 1 warning in 4.14s
```

Et dans `TP/TP4` :

```
> maintai-predict 72 6 85 15000
Probabilité de panne : 95 % (ALERTE)
```

Placez-vous dans un autre dossier (`cd %TEMP%`) et lancez `maintai-predict 72 6 85 15000`, puis `python -c "import maintai; print(maintai.__file__)"`. Qu'affichent ces deux commandes ? Où Python trouve-t-il le code de `maintai` ?

```
Probabilité de panne : 95 % (ALERTE)
C:\Users\...\TP\TP4\maintai\__init__.py
```

La commande marche depuis n'importe quel dossier, et `maintai.__file__` pointe **vers notre dossier de travail `TP\TP4\maintai`**, pas vers une copie. `pip install -e .` a déposé dans `.venv\Lib\site-packages` un fichier `__editable__.maintai-0.2.0.pth` et un « finder ». À chaque démarrage, Python lit ces fichiers, qui lui disent de chercher `maintai` dans `TP\TP4`. Le modèle, lui, est trouvé grâce à `ROOT` dans `config.py`, qui est calculé à partir de l'emplacement de `config.py` (donc `TP\TP4\models`).

Modifiez le message affiché par `maintai/cli.py`, puis relancez `maintai-predict` sans réinstaller. Le changement est-il visible ? Pourquoi ?

```
[modifié] Probabilité de panne : 95 % (ALERTE)
```

**Oui, immédiatement.** En mode éditable, le package n'est pas copié : site-packages contient un **lien** vers notre dossier, et Python relit nos fichiers sources à chaque lancement. Seuls les changements de `pyproject.toml` (une nouvelle dépendance, une nouvelle commande) demandent de relancer `pip install -e .`, parce que le `.exe` et les métadonnées sont créés à l'installation.

**Streamlit sans `python -m`** : `streamlit run ui/app.py` fonctionne maintenant. `maintai` est installé, donc importable quel que soit le dossier mis dans `sys.path`.

## 3. Sprint 2 : construire et installer le wheel

Sortie de `dir dist` après `python -m build` :

```
Successfully built maintai-0.2.0.tar.gz and maintai-0.2.0-py3-none-any.whl

11/11/2026  19:07            12 361 maintai-0.2.0.tar.gz
11/11/2026  19:07            11 641 maintai-0.2.0-py3-none-any.whl
```

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

**Non** : ni le modèle (`models/`), ni les tests (`tests/`), ni `ui/`, ni `web/`, ni les données. `[tool.setuptools.packages.find] include = ["maintai*"]` ne fait entrer que le dossier `maintai/` (et `maintai/api/`). Le wheel livre **le code**. Le modèle est un artefact produit par l'entraînement : il change à chaque réentraînement et se livre séparément. Les tests et l'interface sont des outils de développement et de démonstration, pas une partie de la bibliothèque. `entry_points.txt` contient la déclaration de `maintai-predict`.

Dans un environnement neuf (`%TEMP%\essai`), installez le wheel et lancez `maintai-predict` :

| Étape | Ce qui s'affiche |
|---|---|
| sans `MAINTAI_MODELS_DIR` | `Modèle introuvable : C:\Users\...\Temp\essai\.venv\Lib\site-packages\models\model.joblib` puis `Entraînez-le (python -m maintai.train) ou indiquez son dossier dans MAINTAI_MODELS_DIR.` (code de sortie 1) |
| avec `MAINTAI_MODELS_DIR` vers vos `models` | Trois `InconsistentVersionWarning: Trying to unpickle estimator StandardScaler (puis LogisticRegression, puis Pipeline) from version 1.8.0 when using version 1.9.1. This might lead to breaking code or invalid results. Use at your own risk.` puis `Probabilité de panne : 95 % (ALERTE)` |
| après `pip install scikit-learn==1.8.0` | `Probabilité de panne : 95 % (ALERTE)`, sans aucun avertissement |

Pourquoi « Modèle introuvable » ? Le chemin par défaut est `ROOT / "models"`, avec `ROOT` = le dossier parent de `maintai/`. Une fois le package installé depuis le wheel, ce parent est **`site-packages`**, où il n'y a pas de dossier `models`.

D'où vient l'avertissement `InconsistentVersionWarning` ? Quelle ligne de `models/model_info.json` permet de le comprendre ?

`pyproject.toml` demande seulement `scikit-learn>=1.5`. Dans l'environnement neuf, pip a donc installé **la dernière version, 1.9.1**. Or `model.joblib` est un objet Python « picklé » par **scikit-learn 1.8.0** : la structure interne des estimateurs peut changer d'une version à l'autre, et scikit-learn prévient que la relecture n'est pas garantie (résultats faux, voire plantage). La ligne qui l'explique :

```json
"sklearn_version": "1.8.0"
```

Installer exactement cette version (celle de `requirements.txt`) supprime l'avertissement. Livrer un modèle, c'est donc livrer **trois choses** : le code (le wheel), le modèle (`models/`) et les versions exactes (`requirements.txt`).

## 4. Questions de compréhension

1. Quelle différence entre `requirements.txt` et la liste `dependencies` de `pyproject.toml` ?
   `requirements.txt` dit « **exactement** » (`==`) : il fige tout l'environnement (y compris pytest, streamlit, build) pour **reproduire** à l'identique l'environnement où le modèle a été entraîné. C'est pour une application ou un déploiement. `dependencies` dit « **au moins** » (`>=`) et ne liste que ce que le code importe : un package doit pouvoir s'installer **à côté d'autres packages** sans imposer de versions exactes, ce qui créerait des conflits. Le premier sert à la reproductibilité, le second à la compatibilité.
2. Quelle différence entre `pip install -e .` et `pip install dist\maintai-0.2.0-py3-none-any.whl` ?
   `-e .` (éditable) pose un **lien** vers le dossier du projet : les modifications du code sont visibles tout de suite, sans réinstaller. C'est pour **développer**. Le wheel est une **copie** figée du code dans `site-packages`, construite à un instant donné : modifier les sources ne change rien tant qu'on ne reconstruit pas et ne réinstalle pas. C'est pour **livrer**, sur une autre machine, sans les sources ni Git.
3. Qu'est-ce qu'un « point d'entrée » (`[project.scripts]`) ? Où pip crée-t-il le fichier `maintai-predict.exe` ?
   C'est la déclaration d'une **commande** associée à une fonction Python : `maintai-predict = "maintai.cli:main"` veut dire « quand on tape `maintai-predict`, importer `maintai.cli` et appeler `main()` ». À l'installation, pip génère un petit lanceur `maintai-predict.exe` dans le dossier **`Scripts`** de l'environnement (`.venv\Scripts\maintai-predict.exe` ; vérifié aussi dans `%TEMP%\essai\.venv\Scripts\`). Ce dossier est dans le `PATH` quand l'environnement est activé.

## 5. Le rendu Git

- Lien de la pull request : … *(à compléter)*
- Le tag `tp4` existe sur GitHub : oui / non
- `git status` avant le commit : `dist/`, `build/` ou `maintai.egg-info/` apparaissaient-ils ? **non** (exclus par le `.gitignore` du starter : `dist/`, `build/`, `*.egg-info/`, `.venv/`, `models/`, `data/*.csv`)

## 6. Ce qui reste flou

…
