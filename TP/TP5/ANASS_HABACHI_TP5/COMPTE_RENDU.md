# Compte rendu · TP5 : suivre les entraînements (MLflow) et versionner les données (DVC)

**Groupe :** G1  ·  **Membres :** Anass Habachi  ·  **Date :** 25/11/2026

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
TP4 : `import maintai` chargeait donc le code du TP4.
Après `pip install -e .` lancé dans le dossier du TP5, `pip show maintai` donne :

```
Version: 0.3.0
Location: ...\.venv\Lib\site-packages
Editable project location: C:\Users\DELL\Documents\maintai-g1\TP\TP5\ANASS_HABACHI_TP5
```

Le package pointe maintenant vers le code du TP5. `Location` est l'endroit où pip enregistre le package (dans
l'environnement), et `Editable project location` est le dossier du code réellement chargé. Le test
`test_installed_version_matches_the_code` vérifie justement que le package installé correspond au code du dossier.

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
====================== 32 passed, 6 warnings in 36.72s ======================
```

Vos runs (au moins quatre), relevés dans `mlflow ui` (mode « Model training ») :

| Commande | recall | precision | accuracy | run_id (8 car.) |
|---|---|---|---|---|
| `python -m maintai.train` | 0.750 | 0.622 | 0.904 | `3f657566` |
| `python -m maintai.train --C 0.01` | 0.691 | 0.653 | 0.908 | `9be23a8b` |
| `python -m maintai.train --threshold 0.2` | 0.838 | 0.543 | 0.882 | `1a0577d6` |
| `python -m maintai.train --model forest` | 0.728 | 0.562 | 0.886 | `c5b1dc51` |
| `python -m maintai.train --threshold 0.15` (notre essai) | 0.875 | 0.500 | 0.864 | `bcfb123f` |

Les cinq runs ont le même `data_md5` (`73e0b7cb…`) et le même `n_train` (4000) : ils ont été entraînés sur les mêmes
données, la comparaison porte donc uniquement sur les réglages. Le seuil par défaut est 0.3. Pour tous les runs, le
baseline (ne jamais prédire de panne) a un recall de 0 et une accuracy de 0.864.

Quel run choisiriez-vous pour MaintAI, et pourquoi ? (Rappel : une panne manquée coûte plus cher qu'une fausse alerte.)

Nous choisissons la régression logistique (C = 1.0) avec le seuil 0.2 (run `1a0577d646b24334b480ca57e3297766`).
Son recall est de 0.838, contre 0.750 pour le réglage par défaut : le modèle ne manque plus qu'environ une panne
sur six, au lieu d'une sur quatre. En échange, la precision baisse (0.543), donc il y a plus de fausses alertes. Une panne
manquée coûtant plus cher qu'une fausse alerte, ce compromis est acceptable.

Notre essai au seuil 0.15 pousse le recall à 0.875, mais la precision tombe à 0.500 : une alerte sur deux est fausse.
Son accuracy (0.864) n'est pas meilleure que celle du baseline. Nous jugeons que le gain (environ 4 pannes détectées
en plus sur 100) ne compense pas autant de fausses alertes. Trop d'alertes inutiles finissent par ne plus être prises
au sérieux par les techniciens.

Les autres runs sont moins bons sur le critère qui compte :
- `--C 0.01` : la régularisation plus forte rend le modèle plus prudent. La precision monte, mais le recall tombe à 0.691.
- `--model forest` : la forêt aléatoire n'est pas meilleure. Elle est en dessous de la régression logistique en recall
  (0.728) comme en precision (0.562). Un modèle plus complexe n'est pas automatiquement meilleur.

L'accuracy n'est pas un bon critère ici : elle baisse justement quand le modèle détecte plus de pannes, car les
pannes sont rares (le baseline atteint déjà 0.864 d'accuracy sans en détecter aucune).

**Bonus : recherche par grille (grid search).** Le module `maintai/grid.py` (`python -m maintai.grid`) lance 30 runs
sur les données v2 (`data_md5` = `93fdeef2…`, 6400 relevés d'entraînement) : régression logistique avec
C ∈ {0.01, 0.1, 0.5, 1, 10} et seuil ∈ {0.15, 0.2, 0.25, 0.3, 0.4} (25 runs), plus la forêt aléatoire avec les 5 seuils
(5 runs). Extrait des résultats, triés par recall :

| Modèle | C | seuil | recall | precision | accuracy |
|---|---|---|---|---|---|
| logreg | 0.01 | 0.15 | 0.893 | 0.470 | 0.858 |
| forest | – | 0.15 | 0.878 | 0.481 | 0.863 |
| logreg | 1.0 | 0.15 | 0.859 | 0.506 | 0.874 |
| logreg | 0.1 | 0.2 | 0.829 | 0.559 | 0.894 |
| logreg | 1.0 | 0.2 | 0.824 | 0.567 | 0.897 |
| logreg | 0.1 | 0.25 | 0.790 | 0.625 | 0.912 |
| logreg | 1.0 | 0.3 | 0.741 | 0.650 | 0.916 |
| logreg | 1.0 | 0.4 | 0.663 | 0.723 | 0.924 |

Ce que la grille montre :
- **Le seuil compte beaucoup plus que C.** À seuil fixé, les valeurs C = 0.5, 1 et 10 donnent exactement les mêmes
  résultats. En revanche, passer du seuil 0.4 au seuil 0.15 fait monter le recall de 0.66 à 0.86 environ.
- **Le compromis recall/precision est toujours le même :** chaque baisse du seuil détecte plus de pannes, mais
  ajoute des fausses alertes. Aucun réglage n'améliore les deux à la fois.
- **La forêt aléatoire n'est jamais la meilleure** à seuil égal, sauf au seuil 0.15, où elle reste derrière la
  régression logistique avec C = 0.01.
- Le choix de l'ADR 004 (régression logistique, seuil 0.2) reste valable sur la v2 : recall 0.824, precision 0.567.

Dans `mlflow ui`, ouvrez le modèle d'un run. Quelle version de scikit-learn est indiquée dans son `requirements.txt` ? Quel problème du TP4 cela règle-t-il ?

Le `requirements.txt` enregistré avec le modèle indique `scikit-learn==1.8.0`, ainsi que les versions exactes de
`numpy` (2.4.4), `pandas` (3.0.2), `scipy` (1.18.1), `skops` (0.16.0) et `mlflow` (3.18.0).
Au TP4, le wheel contenait le code mais pas le modèle, et un modèle scikit-learn sauvegardé n'est fiable qu'avec la
même version de scikit-learn que celle de l'entraînement. Rien ne liait le fichier `model.joblib` aux versions qui
l'avaient produit. Désormais, chaque modèle enregistré par MLflow est accompagné de la liste exacte des bibliothèques
nécessaires pour le recharger et le réutiliser à l'identique.

Où MLflow enregistre-t-il les runs sur votre disque ? Ces fichiers vont-ils dans Git ? Pourquoi ?

Dans le dossier du TP5, à deux endroits :
- `mlflow.db`, une base SQLite qui contient les expériences, les runs, les paramètres et les métriques ;
- `mlruns/`, qui contient les artefacts, c'est-à-dire les fichiers des modèles et leur `requirements.txt`
  (par exemple `mlruns/1/models/.../artifacts/`).

Ces fichiers ne vont pas dans Git : `mlflow.db` et `mlruns/` sont listés dans le `.gitignore`. Ce sont des fichiers
générés, binaires et volumineux, qui grossissent à chaque entraînement. Git sert à versionner le code source, pas les
résultats d'exécution. Ces fichiers sont aussi propres à chaque machine.

## 3. Sprint 2 : DVC

Contenu de `data/sensors.csv.dvc` après `dvc add data/sensors.csv` :

```
outs:
- md5: 73e0b7cb3c6f795c70c3ddf970b99c15
  size: 126815
  hash: md5
  path: sensors.csv
```

Comparez la valeur `md5` de ce fichier au paramètre `data_md5` de votre dernier run MLflow. Que constatez-vous ?

Les deux valeurs sont identiques : `73e0b7cb3c6f795c70c3ddf970b99c15`. DVC et `file_md5` calculent la même
empreinte sur le même fichier. C'est ce qui relie un run MLflow à une version précise des données : à partir du
`data_md5` d'un run, on retrouve le commit Git dont le reçu `.dvc` porte ce md5, puis `dvc checkout` restaure
exactement les données qui ont servi à l'entraînement.

Pourquoi `data/sensors.csv` ne va pas dans Git, alors que `data/sensors.csv.dvc` y va ?

`data/sensors.csv` est un fichier de données. Il peut être volumineux (ici 127 Ko, mais en pratique des centaines de
Mo), et Git gère mal les gros fichiers en les gardant à chaque version pour toujours. Il est donc ignoré par Git
(`data/*.csv` dans le `.gitignore`) et confié à DVC, qui le stocke dans son cache puis dans le stockage.
`data/sensors.csv.dvc` n'est qu'un reçu de quelques lignes (md5 et taille). Il est léger et versionné par Git : chaque
commit sait ainsi quelle version des données va avec quel code.

Après `python -m maintai.dataset --n 8000 --seed 7`, que dit `dvc status` ?

```
data\sensors.csv.dvc:
	changed outs:
		modified:           data\sensors.csv
```

DVC détecte que le fichier ne correspond plus au reçu : son md5 a changé depuis le dernier `dvc add`.

| Version | Commit Git (`git log --oneline`) | md5 (8 premiers caractères) | Nombre de lignes |
|---|---|---|---|
| v1 | `52cbd65 Données v1` | 73e0b7cb | 5000 |
| v2 | `7258c49 Données v2` | 93fdeef2 | 8000 |

Revenez à la v1 (`git checkout <commit> -- data/sensors.csv.dvc`, puis `dvc checkout`). Combien de lignes contient `data/sensors.csv` ? Puis revenez à la v2.

Après `git checkout 52cbd65 -- data/sensors.csv.dvc` puis `dvc checkout`, `data/sensors.csv` contient 5000 lignes :
c'est bien la v1. `git status` montre le reçu `.dvc` modifié, car c'est l'ancien reçu. Nous ne l'avons pas commité.
Après `git checkout HEAD -- data/sensors.csv.dvc` puis `dvc checkout`, on retrouve les 8000 lignes de la v2.
Git choisit la version (le reçu), et DVC remet le bon fichier en place à partir de son cache.

Supprimez `data/sensors.csv` et le dossier `.dvc/cache`, puis lancez `dvc pull`. Que se passe-t-il ?

```
A       data\sensors.csv
1 file fetched and 1 file added
```

Sans le fichier et sans le cache, `dvc pull` lit le reçu `data/sensors.csv.dvc`, récupère dans le stockage le fichier
qui a ce md5, le replace dans le cache puis dans `data/`. On retrouve 8000 lignes, avec le md5 `93fdeef2…` : les
données v2 sont restaurées. C'est la situation d'un coéquipier qui clone le dépôt : il obtient le code et les reçus
avec Git, puis les données avec `dvc pull`.

## 4. Relier modèle et données

Entraînez un modèle sur la v2. Dans `mlflow ui`, comparez ce run à celui de la v1 avec les mêmes réglages :

| Run | data_md5 (8 caractères) | n_train | recall | precision |
|---|---|---|---|---|
| v1 (`3f657566`) | 73e0b7cb | 4000 | 0.750 | 0.622 |
| v2 (`4496701a`) | 93fdeef2 | 6400 | 0.741 | 0.650 |

Mêmes réglages pour les deux : régression logistique, C = 1.0, seuil 0.3.

Peut-on dire que le modèle v2 est « meilleur » ? Pourquoi faut-il être prudent en comparant deux runs entraînés sur des données différentes ?

Non. Le run v2 a une precision un peu meilleure (0.650 contre 0.622), mais un recall un peu plus bas (0.741 contre
0.750). Sur le critère qui compte pour MaintAI, il n'est pas meilleur, et les écarts sont faibles.

Surtout, les deux runs ne sont pas évalués sur les mêmes données : chaque version a son propre jeu de test (1000
relevés pour la v1, 1600 pour la v2), tiré d'un jeu généré avec une autre graine. Les données de la v2 n'ont pas non
plus exactement le même taux de panne. Une différence de métriques peut donc venir des données de test, et non du
modèle. Pour comparer deux modèles honnêtement, il faut les évaluer sur le même jeu de test. C'est pourquoi le
`data_md5` est enregistré dans chaque run : il permet de ne comparer que des runs entraînés et évalués sur les mêmes
données.

## 5. Décision : l'ADR 004

Voir `docs/adr/004-choix-du-modele.md` : régression logistique (C = 1.0), seuil 0.2, run
`1a0577d646b24334b480ca57e3297766`, données `data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15` (v1).

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
   Le stockage est un dossier de notre PC (`C:/Users/DELL/dvc-stockage`). Son chemin n'a de sens que sur cette machine,
   donc il ne doit pas aller dans Git. Avec `--local`, il est écrit dans `.dvc/config.local`, qui est ignoré par Git.
   Pour que tout le groupe partage les mêmes données, il faudrait un stockage accessible à tous (S3, Google Drive, un
   serveur partagé), ajouté sans `--local` pour que sa configuration soit commitée dans `.dvc/config`. Chacun pourrait
   alors faire `dvc pull`.
3. Livrer un modèle, c'est trois choses (TP4). Lesquelles, et où sont-elles maintenant ?
   Le code, le modèle entraîné et les versions exactes des bibliothèques. Aujourd'hui :
   - le code est dans **Git** (et dans le wheel du TP4) ;
   - le modèle est dans **MLflow**, sous la forme d'un run identifié par son `run_id` ;
   - les versions exactes sont dans **MLflow**, dans le `requirements.txt` enregistré avec le modèle.

   S'y ajoutent les données d'entraînement, dans **DVC** : le reçu est dans Git, le fichier est dans le stockage.
   Le `data_md5` du run fait le lien entre le modèle et ces données.

## 7. Le rendu Git

- Lien de la pull request : https://github.com/Anas-7bx/maintai-g1/pull/13
- Le tag `tp5` existe sur GitHub : oui / non
- `git status` avant le commit : `mlflow.db`, `mlruns/`, `data/sensors.csv` ou `.dvc/cache` apparaissaient-ils ? non.
  Ils sont tous exclus par le `.gitignore` (et `.dvc/cache`, `.dvc/config.local` par `.dvc/.gitignore`) : `git status`
  était vide après les entraînements, `dvc add` et `dvc push`.

## 8. Ce qui reste flou

1. **Choisir le seuil.** Entre 0.2 et 0.15, il n'y a pas de bonne réponse unique dans le tableau : tout dépend du
   nombre de fausses alertes que l'équipe de maintenance peut accepter. Je ne sais pas encore comment fixer cette
   limite avec un vrai chiffre (par exemple le coût d'une panne comparé au coût d'une inspection inutile).
2. **Le stockage DVC en équipe.** Dans ce TP, le stockage est un dossier de mon PC. Je ne vois pas encore bien comment
   le groupe partagerait les mêmes données en pratique : quel service utiliser (Google Drive, S3…), comment donner
   l'accès à chacun, et comment éviter que deux membres poussent deux versions différentes en même temps.
