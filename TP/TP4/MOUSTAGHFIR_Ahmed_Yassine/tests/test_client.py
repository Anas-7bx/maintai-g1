"""Le client appelle l'application de test, sans uvicorn."""

import pytest

from maintai.client import APIError, MaintaiClient

VALID = {
    "temperature_c": 60.0,
    "vibration_mm_s": 2.0,
    "load_pct": 50.0,
    "runtime_hours": 5000,
}


def test_predict_returns_probability(client):
    resultat = MaintaiClient(api_key="test-key", http=client).predict(VALID)
    assert 0 <= resultat["failure_probability"] <= 1
    assert isinstance(resultat["alert"], bool)


def test_missing_key_raises(client):
    with pytest.raises(APIError) as exc:
        MaintaiClient(http=client).predict(VALID)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Clé API absente ou invalide"


def test_invalid_reading_raises(client):
    with pytest.raises(APIError) as exc:
        MaintaiClient(api_key="test-key", http=client).predict(
            {**VALID, "temperature_c": 500}
        )
    assert exc.value.status_code == 422
