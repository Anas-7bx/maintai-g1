"""Commande maintai-predict : une prédiction sans lancer l'API.

Usage : maintai-predict 72 6 85 15000
"""

import argparse

from maintai.config import get_settings
from maintai.predict import Predictor


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Prédit une probabilité de panne à partir de quatre mesures."
    )
    parser.add_argument("temperature_c", type=float)
    parser.add_argument("vibration_mm_s", type=float)
    parser.add_argument("load_pct", type=float)
    parser.add_argument("runtime_hours", type=float)
    args = parser.parse_args(argv)

    try:
        predictor = Predictor.load(get_settings())
    except FileNotFoundError:
        print("Modèle introuvable")
        return

    resultat = predictor.predict(
        {
            "temperature_c": args.temperature_c,
            "vibration_mm_s": args.vibration_mm_s,
            "load_pct": args.load_pct,
            "runtime_hours": args.runtime_hours,
        }
    )
    pourcentage = round(resultat["failure_probability"] * 100)
    texte = f"Probabilité de panne : {pourcentage} %"
    if resultat["alert"]:
        texte += " (ALERTE)"
    print(texte)
