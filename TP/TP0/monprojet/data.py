
"""Chargement et découpage des données."""

import pandas as pd
from sklearn.model_selection import train_test_split

from monprojet import config


def load_data(path=None) -> pd.DataFrame:
    """Lit le fichier CSV et renvoie un DataFrame."""

    # Utiliser le chemin fourni ou celui de config.py
    csv_path = path if path is not None else config.DATA_PATH

    # Charger le fichier CSV
    df = pd.read_csv(csv_path)

    # Vérifier que la colonne cible existe
    if config.TARGET not in df.columns:
        raise ValueError(
            f"La colonne cible '{config.TARGET}' est absente du fichier CSV."
        )

    # Supprimer les lignes où la cible est manquante
    df = df.dropna(subset=[config.TARGET])

    return df


def feature_columns(df: pd.DataFrame) -> list:
    """Renvoie les colonnes utilisées comme variables d'entrée."""

    if config.FEATURES is not None:
        return list(config.FEATURES)

    excluded = {config.TARGET, config.TIME_COLUMN}

    return [c for c in df.columns if c not in excluded]


def split(df: pd.DataFrame):
    """Renvoie X_train, X_test, y_train, y_test."""

    # Vérification du découpage chronologique
    if config.SPLIT == "chronologique":

        if config.TIME_COLUMN is None:
            raise ValueError(
                "TIME_COLUMN doit être définie pour un découpage chronologique."
            )

        # Copier les données pour ne pas modifier le DataFrame original
        df = df.copy()

        # Convertir la colonne temporelle en datetime
        df[config.TIME_COLUMN] = pd.to_datetime(
            df[config.TIME_COLUMN]
        )

        # Trier les données de la plus ancienne à la plus récente
        df = df.sort_values(by=config.TIME_COLUMN)

    # Séparer les variables explicatives et la cible
    X = df[feature_columns(df)]
    y = df[config.TARGET]

    # Cas 1 : découpage aléatoire
    if config.SPLIT == "random":

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=config.TEST_SIZE,
            random_state=config.SEED,
            stratify=y if config.TASK == "classification" else None
        )

    # Cas 2 : découpage chronologique
    elif config.SPLIT == "chronologique":

        n_train = int(len(df) * (1 - config.TEST_SIZE))

        X_train = X.iloc[:n_train]
        X_test = X.iloc[n_train:]

        y_train = y.iloc[:n_train]
        y_test = y.iloc[n_train:]

    else:
        raise ValueError(
            f"Type de découpage inconnu : {config.SPLIT}"
        )

    return X_train, X_test, y_train, y_test
