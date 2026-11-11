"""La commande, appelée comme une fonction : pas besoin de l'installer."""


def test_predict_prints_alert(capsys, trained_model):
    from maintai.cli import main

    main(["72", "6", "85", "15000"])
    sortie = capsys.readouterr().out
    assert sortie.startswith("Probabilité de panne : ")
    assert "ALERTE" in sortie


def test_missing_model_is_reported(capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MAINTAI_MODELS_DIR", str(tmp_path / "absent"))
    from maintai.cli import main

    main(["72", "6", "85", "15000"])
    assert capsys.readouterr().out.strip() == "Modèle introuvable"
