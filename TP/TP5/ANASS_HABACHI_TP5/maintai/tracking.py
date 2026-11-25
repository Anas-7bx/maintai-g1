"""Suivi des entraînements avec MLflow : chaque entraînement devient un « run » qu'on peut comparer.

Les runs sont enregistrés dans mlflow.db (dossier courant) ; on les regarde avec : mlflow ui
"""
import hashlib
import os
from pathlib import Path

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")  # coupe un message d'information de MLflow

import mlflow
import mlflow.sklearn

EXPERIMENT = "maintai"
TRUSTED_TYPES = ["sklearn.tree._tree.Tree"]  # nécessaire pour --model forest


def file_md5(path: Path) -> str:
    """Empreinte du fichier de données : la même que celle que DVC écrit dans le fichier .dvc."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


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
