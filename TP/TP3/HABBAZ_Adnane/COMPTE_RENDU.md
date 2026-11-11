# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** …  ·  **Membres :** …  ·  **Date :** …

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
5 failed, 18 passed, 1 warning in 5.12s
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

FAILED tests/test_client.py::test_client_returns_prediction - NotImplementedError: TP3 sprint 2 : MaintaiClient.predict
FAILED tests/test_client.py::test_client_wrong_key_raises_401 - NotImplementedError: TP3 sprint 2 : MaintaiClient.predict
FAILED tests/test_client.py::test_client_bad_reading_raises_422 - NotImplementedError: TP3 sprint 2 : MaintaiClient.predict
FAILED tests/test_ui.py::test_ui_shows_the_data - IndexError: list index out of range
FAILED tests/test_ui.py::test_ui_shows_the_prediction - IndexError: list index out of range

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
from maintai.client import APIError, MaintaiClient
ModuleNotFoundError: No module named 'maintai'
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

`python -m` lance Streamlit comme module depuis le projet : le dossier courant est alors dans le chemin de recherche Python, donc `maintai` est importable. Avec `streamlit run`, le chemin de recherche ne contient pas forcément la racine du projet.

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

```python
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

```

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000 |
| Taux de panne | 13.6 % |
| Température moyenne | 59.8 °C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

Le taux de panne augmente nettement avec la vibration : environ 2 % dans la première tranche, puis plus de 80 % dans les tranches élevées; les dernières tranches observées atteignent 100 %.

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

Le message `relance` réapparaît dans le terminal après le déplacement du curseur. Streamlit réexécute le script de haut en bas après une interaction.

À quoi sert `@st.cache_data` sur la fonction `charger` ?

`@st.cache_data` conserve le résultat de la lecture du CSV pour éviter de le relire à chaque réexécution.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
    """Envoie un relevé ; lève APIError si l'API refuse."""
    headers = {"X-API-Key": self.api_key} if self.api_key else {}
    response = self.http.post("/v1/predict", json=reading, headers=headers)
    if response.status_code != 200:
        raise APIError(response.status_code, response.json().get("detail"))
    return response.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
23 passed, 1 warning in 4.27s
```

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | Probabilité de panne : 95 %; alerte affichée. L'API renvoie 0.9475 et `alert=True`. |
| valeurs par défaut, fausse clé | Erreur API (401) : clé absente ou invalide. |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | « API injoignable : impossible de joindre l'API. » |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

Streamlit envoie la requête depuis le serveur Python avec `httpx`, pas depuis le navigateur. CORS protège les requêtes navigateur entre origines; il ne s'applique pas à cet appel serveur-à-serveur.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
    En TP2, le JavaScript du navigateur envoie la requête avec `fetch`. En TP3, le code Python côté serveur Streamlit l'envoie avec `httpx`.
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
    Ils utilisent le `TestClient` de FastAPI, injecté dans `MaintaiClient`; la requête est traitée directement par l'application en mémoire.
3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
    Pour une démonstration rapide, je choisirais Streamlit, car les graphiques et contrôles sont faciles à faire évoluer. Pour un outil durable utilisé par les techniciens, je choisirais une interface web dédiée, plus libre à adapter aux tâches et aux écrans utilisés sur le terrain.

## 6. Le rendu Git

- Lien de la pull request : non créée; ce dossier ne contient pas de dépôt Git.
- Le tag `tp3` existe sur GitHub : non vérifiable depuis ce dossier sans dépôt Git.
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? non vérifiable; `git status` indique que le dossier n'est pas un dépôt Git.

## 7. Ce qui reste flou

À compléter par les membres selon les questions qui restent après le TP.
