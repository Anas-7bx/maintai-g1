"""Interface Streamlit de MaintAI : explorer les données, puis demander une prédiction à l'API.

Lancement (depuis la racine du projet) : python -m streamlit run ui/app.py
"""
import httpx
import pandas as pd
import streamlit as st

from maintai.client import APIError, MaintaiClient
from maintai.config import FEATURES, get_settings

st.set_page_config(page_title="MaintAI", page_icon="🔧")
st.title("MaintAI · prédiction de panne")


@st.cache_data
def charger(path) -> pd.DataFrame:
    # Lu une seule fois : Streamlit relance tout le script à chaque clic
    return pd.read_csv(path)


with st.sidebar:
    url = st.text_input("URL de l'API", "http://localhost:8000")
    cle = st.text_input("Clé API", type="password")

onglet_donnees, onglet_prediction = st.tabs(["Données", "Prédiction"])

# Sprint 1 : explorer les données
with onglet_donnees:
    df = charger(get_settings().data_path)

    if {"failure", "temperature_c"}.issubset(df.columns):
        colonnes = st.columns(3)
        colonnes[0].metric("Nombre de relevés", len(df))
        colonnes[1].metric("Taux de panne", f"{df['failure'].mean() * 100:.1f}%")
        colonnes[2].metric("Température moyenne", f"{df['temperature_c'].mean():.1f} °C")

    variable = st.selectbox("Choisir une variable", FEATURES)
    if variable in df.columns:
        bins = pd.cut(df[variable], bins=10, duplicates="drop")
        taux_panne = df.groupby(bins)["failure"].mean().mul(100)
        taux_panne.index = taux_panne.index.astype(str)
        st.bar_chart(taux_panne)

    if {"temperature_c", "vibration_mm_s", "failure"}.issubset(df.columns):
        st.scatter_chart(df, x="temperature_c", y="vibration_mm_s", color="failure")


# Sprint 2 : demander une prédiction à l'API
with onglet_prediction:
    with st.form("releve"):
        releve = {
            "temperature_c": st.slider("Température (°C)", -40.0, 150.0, 72.0),
            "vibration_mm_s": st.slider("Vibration (mm/s)", 0.0, 50.0, 6.0),
            "load_pct": st.slider("Charge (%)", 0.0, 100.0, 85.0),
            "runtime_hours": st.number_input("Heures de fonctionnement", 0, 100_000, 15000),
        }
        envoye = st.form_submit_button("Prédire")

    if envoye:
        try:
            client = MaintaiClient(url, api_key=cle)
            reponse = client.predict(releve)
        except APIError as exc:
            st.warning(f"Erreur API ({exc.status_code}) : {exc.detail}")
        except httpx.HTTPError:
            st.error("API injoignable : impossible de joindre l'API.")
        else:
            pourcentage = reponse["failure_probability"] * 100
            st.metric("Probabilité de panne", f"{pourcentage:.0f} %")
            if reponse["alert"]:
                st.error("ALERTE : forte probabilité de panne.")
            else:
                st.success("Le système ne détecte pas de risque élevé.")
