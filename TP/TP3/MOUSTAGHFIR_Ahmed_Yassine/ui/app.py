"""Interface Streamlit de MaintAI : données et prédiction.

Lancement : python -m streamlit run ui/app.py
"""

import httpx
import pandas as pd
import streamlit as st

from maintai.client import APIError, MaintaiClient
from maintai.config import FEATURES, get_settings


st.set_page_config(page_title="MaintAI", layout="wide")
st.title("MaintAI")

with st.sidebar:
    st.header("API")
    url = st.text_input("URL de l'API", "http://127.0.0.1:8000")
    cle = st.text_input("Clé API", type="password")


@st.cache_data
def charger(chemin: str) -> pd.DataFrame:
    """Le CSV n'est relu que si le chemin change, pas à chaque clic."""
    return pd.read_csv(chemin)


df = charger(str(get_settings().data_path))
onglet_donnees, onglet_prediction = st.tabs(["Données", "Prédiction"])

with onglet_donnees:
    c1, c2, c3 = st.columns(3)
    c1.metric("Relevés", len(df))
    c2.metric("Taux de panne", f"{df['failure'].mean():.1%}")
    c3.metric("Température moyenne", f"{df['temperature_c'].mean():.1f} °C")

    variable = st.selectbox("Variable", FEATURES)
    tranches = pd.cut(df[variable], bins=10)
    taux = df.groupby(tranches, observed=True)["failure"].mean()
    etiquettes = [round(intervalle.mid, 1) for intervalle in taux.index]
    st.bar_chart(
        pd.Series(taux.to_numpy(), index=etiquettes, name="taux de panne"),
    )
    nuage = df.copy()
    nuage["panne"] = nuage["failure"].map({0: "non", 1: "oui"})
    st.scatter_chart(
        nuage,
        x="temperature_c",
        y="vibration_mm_s",
        color="panne",
    )

with onglet_prediction:
    with st.form("releve"):
        temperature = st.slider("Température (°C)", -40.0, 150.0, 72.0)
        vibration = st.slider("Vibration (mm/s)", 0.0, 50.0, 6.0)
        charge = st.slider("Charge (%)", 0.0, 150.0, 85.0)
        heures = st.slider("Heures de fonctionnement", 0.0, 100_000.0, 15_000.0)
        envoye = st.form_submit_button("Prédire")

    if envoye:
        client = MaintaiClient(api_key=cle, http=httpx.Client(base_url=url))
        lecture = {
            "temperature_c": temperature,
            "vibration_mm_s": vibration,
            "load_pct": charge,
            "runtime_hours": heures,
        }
        try:
            resultat = client.predict(lecture)
        except APIError as exc:
            st.error(f"Erreur {exc.status_code} : {exc.detail}")
        except httpx.HTTPError:
            st.error("API injoignable (arrêtée, ou mauvaise URL)")
        else:
            pourcentage = round(resultat["failure_probability"] * 100)
            texte = f"Probabilité de panne : {pourcentage} %"
            if resultat["alert"]:
                st.error(f"{texte} (ALERTE)")
            else:
                st.success(texte)
