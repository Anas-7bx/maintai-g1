"""La page, sans navigateur : AppTest vérifie l'interface, pas l'API."""

from pathlib import Path

import httpx
import pandas as pd
from streamlit.testing.v1 import AppTest

from maintai.client import APIError, MaintaiClient
from maintai.config import FEATURES

APP = Path(__file__).resolve().parents[1] / "ui" / "app.py"


def test_premier_indicateur_est_le_nombre_de_releves(settings_env):
    at = AppTest.from_file(str(APP)).run()
    assert not at.exception
    n = len(pd.read_csv(settings_env / "sensors.csv"))
    assert at.metric[0].label == "Relevés"
    assert int(at.metric[0].value) == n
    assert at.selectbox[0].options == FEATURES
    # barres et nuage de points : Streamlit les rend en graphiques Vega-Lite
    assert len(at.get("vega_lite_chart")) == 2


def test_prediction_affiche_proba_401_et_api_injoignable(settings_env, monkeypatch):
    etat = {"i": 0}

    def predict(self, reading):
        etat["i"] += 1
        if etat["i"] == 1:
            return {
                "failure_probability": 0.9475,
                "alert": True,
                "threshold": 0.3,
                "model_version": "test",
            }
        if etat["i"] == 2:
            raise APIError(401, "Clé API absente ou invalide")
        raise httpx.ConnectError("connexion refusée")

    monkeypatch.setattr(MaintaiClient, "predict", predict)
    at = AppTest.from_file(str(APP)).run()
    bouton = next(b for b in at.button if b.label == "Prédire")

    bouton.click().run()
    assert not at.exception
    assert "95 %" in at.error[0].value
    assert "ALERTE" in at.error[0].value

    bouton.click().run()
    assert "401" in at.error[0].value

    bouton.click().run()
    assert "API injoignable" in at.error[0].value
