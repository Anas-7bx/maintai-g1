# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** …  ·  **Membres :** …  ·  **Date :** 25/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP5.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP5`)

Dernière ligne de `python -m pytest` après `pip install -r requirements.txt` et `pip install -e .` :

```
================= 5 failed, 27 passed, 2 warnings in 19.89s =================
```

Quels tests échouent, et pourquoi ?

Les cinq tests de `tests/test_tracking.py` échouent : `test_training_creates_a_run`, `test_run_records_metrics`,
`test_run_records_data_version`, `test_run_stores_the_model` et `test_options_change_the_run`.
Ils échouent tous avec le même message, « aucun run MLflow : log_run n'a rien enregistré ». La fonction `log_run` de
`maintai/tracking.py` n'est encore qu'un TODO qui renvoie `""` : aucun run n'est enregistré dans MLflow, donc
`mlflow.search_runs` renvoie un tableau vide. Les 27 autres tests (API, client, CLI, données, package, sécurité,
entraînement, interface) ne dépendent pas de MLflow et passent.

Avant `pip install -e .`, où pointait le package `maintai` installé dans l'environnement ? Et après ?

On réutilise l'environnement du TP4. Avant, le package `maintai` était installé en mode éditable depuis le dossier du
TP4 (`Editable project location` = dossier `TP4`) : `import maintai` chargeait donc le code du TP4.
Après `pip install -e .` lancé dans `TP5`, `pip show maintai` donne :

```
Version: 0.3.0
Location: ...\.venv\Lib\site-packages
Editable project location: C:\Users\DELL\Downloads\TP5
```

Le package pointe maintenant vers le code du TP5. Le test `test_installed_version_matches_the_code` vérifie justement
que le package installé correspond au code du dossier.

## 2. Sprint 1 : MLflow

Votre fonction `log_run` (`maintai/tracking.py`) :

```python
def log_run(params: dict, metrics: dict, model, X_example, data_path: Path) -> str:
    """Enregistre un entraînement : paramètres, version des données, métriques et modèle. Renvoie l'id du run."""
    # 1. toutes les runs de MaintAI sont rangées dans la même expérience
    mlflow.set_experiment(EXPERIMENT)
    # 2. tout ce qui est enregistré dans le with appartient à ce run
    with mlflow.start_run() as run:
        # 3a. les réglages : model, threshold, n_train, C
        mlflow.log_params(params)
        # 3b. la version des données : le même md5 que DVC écrira dans le fichier .dvc
        mlflow.log_param("data_md5", file_md5(data_path))
        # 3c. les résultats : recall, precision, accuracy, baseline_recall...
        mlflow.log_metrics(metrics)
        # 3d. le modèle, avec ses versions exactes de bibliothèques (requirements.txt)
        mlflow.sklearn.log_model(
            model,
            name="model",
            input_example=X_example,
            skops_trusted_types=TRUSTED_TYPES,  # sinon --model forest échoue
        )
    # 4. l'identifiant du run, affiché par train.py après « Run MLflow : »
    return run.info.run_id
```

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
====================== 32 passed, 6 warnings in 34.31s ======================
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy |
|---|---|---|---|
| `python -m maintai.train` | 0.750 | 0.622 | 0.904 |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 |
| `python -m maintai.train --threshold 0.15` (notre essai) | 0.875 | 0.500 | 0.864 |

Les quatre runs ont le même `data_md5` (`73e0b7cb…`) et le même `n_train` (4000) : ils ont été entraînés sur les mêmes
données, la comparaison porte donc uniquement sur les réglages. Le seuil par défaut est 0.3. Pour toutes les runs, le
baseline (ne jamais prédire de panne) a un recall de 0.

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

Nous choisissons la régression logistique (C = 1.0) avec le seuil 0.2 (run `674d02c96ccf4ef783fbc32af754da65`). C'est
le meilleur recall : 0.838, contre 0.750 pour le réglage par défaut. Le modèle ne manque plus qu'environ une panne
sur six, au lieu d'une sur quatre. En échange, la precision baisse (0.543) : il y a plus de fausses alertes. Une panne
manquée coûtant plus cher qu'une fausse alerte, ce compromis est acceptable.

Les autres runs sont moins bons sur le critère qui compte :
- `--C 0.01` : la régularisation plus forte rend le modèle plus prudent. La precision monte, mais le recall tombe à 0.691.
- `--model forest` : la forêt aléatoire n'est pas meilleure. Elle est en dessous de la régression logistique en recall
  (0.728) comme en precision (0.562). Un modèle plus complexe n'est pas automatiquement meilleur.

L'accuracy n'est pas un bon critère ici : elle est la plus basse justement pour le run qui détecte le plus de pannes,
car les pannes sont rares (le baseline atteint déjà environ 0.86 d'accuracy sans en détecter aucune).

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

Le `requirements.txt` enregistré avec le modèle indique `scikit-learn==1.8.0`, ainsi que les versions exactes de
`numpy` (2.4.4), `pandas` (3.0.2), `scipy`, `skops` et `mlflow` (3.18.0).
Au TP4, le wheel contenait le code mais pas le modèle, et un modèle scikit-learn sauvegardé n'est fiable qu'avec la
même version de scikit-learn que celle de l'entraînement. Rien ne liait le fichier `model.joblib` aux versions qui
l'avaient produit. Désormais, chaque modèle enregistré par MLflow est accompagné de la liste exacte des bibliothèques
nécessaires pour le recharger et le réutiliser à l'identique.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Dans le dossier `TP5`, à deux endroits :
- `mlflow.db`, une base SQLite qui contient les expériences, les runs, les paramètres et les métriques ;
- `mlruns/`, qui contient les artefacts, c'est-à-dire les fichiers des modèles et leur `requirements.txt`
  (par exemple `mlruns/1/models/.../artifacts/`).

Ces fichiers ne vont pas dans Git : `mlflow.db` et `mlruns/` sont listés dans le `.gitignore`. Ce sont des fichiers
générés, binaires et volumineux, qui grossissent à chaque entraînement. Git sert à versionner le code source, pas les
résultats d'exécution. Ces fichiers sont aussi propres à chaque machine.

## 3. Sprint 2 : DVC

> À compléter après le sprint 2.

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
(collez ici)
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

…

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

…

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
(collez ici)
```

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | | 73e0b7cb | 5000 |
| v2 | | | |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

…

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

…

## 4. Relier modèle et données

> À compléter après le sprint 2.

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 | 73e0b7cb | 4000 | 0.750 | 0.622 |
| v2 | | | | |

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

…

## 5. Décision : l'ADR 004

Dans `docs/adr/004-choix-du-modele.md` : le modèle et le seuil retenus, à partir de votre tableau MLflow. Indiquez l'identifiant du run et le `data_md5` de la version des données utilisée.

## 6. Questions de compréhension

1. Quelle différence entre Git, DVC et MLflow ? Que versionne chacun ?
   - **Git** versionne le code, plus un « reçu » de quelques lignes par fichier de données (le fichier `.dvc`, avec le md5
     et la taille).
   - **DVC** versionne les fichiers de données eux-mêmes. Il les garde hors de Git, dans un cache local puis dans un
     stockage partagé, et les retrouve grâce au reçu.
   - **MLflow** garde la trace de chaque entraînement (run) : ses paramètres, l'empreinte des données (`data_md5`), ses
     métriques et le modèle avec les versions exactes des bibliothèques.

   Le DevOps gère une seule chose qui change, le code. Le MLOps en gère trois : le code (Git), les données (DVC) et le
   modèle (MLflow).
2. Pourquoi le stockage DVC est-il ajouté avec `--local` dans ce TP ? Que faudrait-il pour que tout le groupe partage les mêmes données ?
   Le stockage est un dossier de notre PC. Son chemin n'a de sens que sur cette machine, donc il ne doit pas aller dans
   Git. Avec `--local`, il est écrit dans `.dvc/config.local`, qui est ignoré par Git. Pour que tout le groupe partage
   les mêmes données, il faudrait un stockage accessible à tous (S3, Google Drive, un serveur partagé), ajouté sans
   `--local` pour que sa configuration soit commitée dans `.dvc/config`. Chacun pourrait alors faire `dvc pull`.
3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
   Le code, le modèle entraîné et les versions exactes des bibliothèques. Aujourd'hui :
   - le code est dans **Git** (et dans le wheel du TP4) ;
   - le modèle est dans **MLflow**, sous la forme d'un run identifié par son `run_id` ;
   - les versions exactes sont dans **MLflow**, dans le `requirements.txt` enregistré avec le modèle.

   S'y ajoutent les données d'entraînement, dans **DVC** : le reçu est dans Git, le fichier est dans le stockage.
   Le `data_md5` du run fait le lien entre le modèle et ces données.

## 7. Le rendu Git

> À compléter lors du rendu.

- Lien de la pull request : …
- Le tag `tp5` existe sur GitHub : oui / non
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? oui / non

## 8. Ce qui reste flou

…
