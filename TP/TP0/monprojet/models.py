
"""Les modèles à comparer.

À vous d'écrire candidates(). Les tests de tests/test_models.py disent ce qui est attendu.
"""
from monprojet import config  # noqa: F401  (config.TASK, config.SEED)

from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor


def candidates() -> dict:
    """Renvoie un dictionnaire {nom: modèle scikit-learn non entraîné}.

    Attendu :
    - le PREMIER modèle est la baseline : le modèle le plus simple possible
      (DummyClassifier pour une classification, DummyRegressor pour une régression) ;
    - au moins trois vrais modèles ensuite, adaptés à config.TASK ;
    - random_state=config.SEED pour les modèles qui ont du hasard.

    Pistes : sklearn.dummy, sklearn.linear_model, sklearn.ensemble, sklearn.neighbors, sklearn.tree.
    """

    # Classification
    if config.TASK == "classification":
        return {
            "baseline": DummyClassifier(
                strategy="most_frequent"
            ),

            "logistic_regression": LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=config.SEED
            ),

            "decision_tree": DecisionTreeClassifier(
                class_weight="balanced",
                random_state=config.SEED
            ),

            "random_forest": RandomForestClassifier(
                n_estimators=100,
                class_weight="balanced",
                random_state=config.SEED
            )
        }

    # Régression
    elif config.TASK == "regression":
        return {
            "baseline": DummyRegressor(
                strategy="mean"
            ),

            "ridge": Ridge(),

            "decision_tree": DecisionTreeRegressor(
                random_state=config.SEED
            ),

            "random_forest": RandomForestRegressor(
                n_estimators=100,
                random_state=config.SEED
            )
        }

    else:
        raise ValueError(
            f"Type de tâche inconnu : {config.TASK}"
        )
