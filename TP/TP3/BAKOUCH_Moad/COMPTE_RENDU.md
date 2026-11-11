# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**Groupe :** G1  ·  **Membres :** Moad Bakouch  ·  **Date :** 11/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
FAILED tests/test_client.py::test_client_returns_prediction - NotImplementedError
FAILED tests/test_client.py::test_client_wrong_key_raises_401 - NotImplementedError
FAILED tests/test_client.py::test_client_bad_reading_raises_422 - NotImplementedError
FAILED tests/test_ui.py::test_ui_shows_the_data - IndexError: list index out of range
FAILED tests/test_ui.py::test_ui_shows_the_prediction - IndexError: list index out of range
5 failed, 18 passed, 1 warning in 2.84s
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

- `tests/test_client.py` (3 tests) : **`NotImplementedError`** (« TP3 sprint 2 : MaintaiClient.predict »). La méthode `predict` du client n'est pas écrite.
- `tests/test_ui.py` (2 tests) : **`IndexError: list index out of range`**. Le test lit `at.metric[0]` (et `at.metric[-1]`), mais la page ne contient encore aucun `st.metric`, seulement des `st.info(...)` : la liste des indicateurs est vide.

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ? (capture `captures/streamlit_run_sans_python_m.png`)

```
ModuleNotFoundError: No module named 'maintai'
Traceback:
File "...\TP3\ui\app.py", line 10, in <module>
    from maintai.client import APIError, MaintaiClient
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

Python cherche les modules dans une liste de dossiers (`sys.path`), et cette liste dépend de la façon de lancer. Avec `streamlit run ui/app.py`, c'est le dossier **du script** (`ui/`) qui est ajouté au chemin, pas la racine du projet. Or le package `maintai/` est à la racine, donc introuvable. Avec `python -m streamlit ...`, Python ajoute le **dossier courant** (`TP/TP3`, la racine du projet) à `sys.path`, et `import maintai` le trouve. C'est le même problème que `python monprojet/train.py` en séance 3. Le TP4 le règle pour de bon en installant `maintai` comme un package.

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

```python
    c1, c2, c3 = st.columns(3)
    c1.metric("Relevés", len(df))
    # failure vaut 0 ou 1 : sa moyenne est la part de pannes
    c2.metric("Taux de panne", f"{df.failure.mean():.1%}")
    c3.metric("Température moyenne", f"{df.temperature_c.mean():.1f} °C")

    variable = st.selectbox("Variable", FEATURES)

    tranches = pd.cut(df[variable], bins=10)
    taux = df.groupby(tranches, observed=True).failure.mean()
    # milieu de chaque tranche : des nombres (triés comme des nombres), pas du texte
    taux.index = [round(i.mid) for i in taux.index]
    taux.name = "taux de panne"
    st.subheader(f"Taux de panne selon {variable}")
    st.bar_chart(taux)

    st.subheader("Température et vibration (500 relevés)")
    echantillon = df.sample(min(500, len(df)), random_state=0).assign(
        panne=lambda d: d.failure.map({0: "non", 1: "oui"})
    )
    st.scatter_chart(echantillon, x="temperature_c", y="vibration_mm_s", color="panne")
```

Capture : `captures/donnees_vibration.png` (barres pour `vibration_mm_s` et nuage de points).

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000 |
| Taux de panne | 13.6% |
| Température moyenne | 59.8 °C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

Il **augmente très fortement, de façon quasi monotone** :

| Vibration (milieu de tranche, mm/s) | ≈1 | ≈3 | ≈6 | ≈8 | ≈10 | ≥12 |
|---|---|---|---|---|---|---|
| Taux de panne | 2 % | 10 % | 32 % | 66 % | 84 % | 100 % |

Pour la température, le taux passe de 0 % (≈27 °C) à environ 37 % (≈85-90 °C) : il monte aussi, mais beaucoup moins. **La vibration est la variable qui compte le plus.** C'est cohérent avec la façon dont les données sont générées (coefficient de 0,6 par mm/s, contre 0,08 par °C). Attention : les dernières tranches de vibration contiennent très peu de relevés (21, 5 et 1). Leur 100 % est peu fiable.

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

Essayé : après le chargement, un changement de variable et deux clics sur « Prédire », le terminal contenait **6** lignes `relance`. `relance` s'affiche **à chaque interaction** : au chargement, à chaque changement de la liste déroulante, à chaque clic. Avec les curseurs du formulaire, `relance` n'apparaît pas tant qu'on n'a pas cliqué sur « Prédire ». C'est la règle de Streamlit : **tout le script est réexécuté de la première à la dernière ligne** à chaque fois qu'un widget change, avec la nouvelle valeur, et Streamlit renvoie la nouvelle page. Le `st.form` regroupe ses widgets pour ne relancer qu'au clic sur le bouton.

À quoi sert `@st.cache_data` sur la fonction `charger` ?

Comme le script est relancé à chaque clic, `pd.read_csv` relirait le fichier à chaque interaction, et la page deviendrait lente. `@st.cache_data` garde en mémoire le résultat de `charger(path)` pour un même argument : le CSV est lu **une seule fois**, puis les relances réutilisent le DataFrame en cache.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
    def predict(self, reading: dict) -> dict:
        """Envoie un relevé ; lève APIError si l'API refuse, httpx.HTTPError si elle est injoignable."""
        headers = {"X-API-Key": self.api_key} if self.api_key else {}
        # self.http et non httpx.post : les tests injectent leur propre client (sans serveur)
        r = self.http.post("/v1/predict", json=reading, headers=headers)
        if r.status_code != 200:
            try:
                detail = r.json().get("detail")
            except ValueError:
                detail = r.text  # réponse qui n'est pas du JSON (proxy, page d'erreur HTML...)
            raise APIError(r.status_code, detail)
        return r.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
23 passed, 1 warning in 3.44s
```

(À la fin du sprint 1 : `4 failed, 19 passed`. Ensuite, `ruff check . --fix` a corrigé deux remarques du starter, I001 et UP017, et `ruff check .` donne `All checks passed!`.)

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`), observé dans Microsoft Edge (captures `captures/prediction_*.png`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | Indicateur « Probabilité de panne : **95 %** » et encadré rouge « **ALERTE** : probabilité au-dessus du seuil 0.3, inspecter la machine » |
| valeurs par défaut, fausse clé | Encadré jaune « **Erreur 401** : Clé API absente ou invalide » |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | Encadré rouge « **API injoignable** : uvicorn est-il lancé ? L'URL est-elle correcte ? » |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

Parce que, dans Streamlit, **ce n'est pas le navigateur qui appelle l'API**. Le code Python de `ui/app.py` s'exécute **sur le serveur Streamlit**, et c'est lui qui envoie la requête à l'API avec httpx. Le navigateur ne parle qu'au serveur Streamlit (8501), sa propre origine. Or CORS est une règle **du navigateur**, qu'il applique au JavaScript d'une page qui appelle une autre origine. Un programme Python, comme `curl.exe`, n'est pas soumis à CORS. Seule la clé API compte.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   Dans le TP2, c'est **le navigateur de l'utilisateur**, qui exécute le JavaScript (`fetch`) de la page : la requête part de la machine de l'utilisateur, d'une origine `localhost:5500`, et elle est soumise à CORS. Dans Streamlit, c'est **le serveur Streamlit**, en Python (`httpx`, via `MaintaiClient`) : le navigateur n'affiche que le résultat.
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   Parce que `MaintaiClient` accepte un client HTTP injecté (`http=`). Les tests lui donnent le `TestClient` de FastAPI, qui envoie les requêtes **directement à l'objet `app` en mémoire**, sans réseau ni port. C'est le même code client et la même API, mais sans serveur à lancer. D'où l'importance d'utiliser `self.http.post` et pas `httpx.post`.
3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   Pour une **démonstration**, **Streamlit** : en quelques lignes de Python on a des indicateurs, des graphiques et un formulaire, sans connaître JavaScript, et c'est prêt en une séance. Pour l'**application d'un technicien**, une **page HTML/JS** (ou une application dédiée) : elle est plus légère, fonctionne sur mobile et tablette à l'atelier, se personnalise librement, et n'exige pas un serveur Python qui relance tout le script à chaque clic. Il faudrait alors gérer correctement la clé (un serveur intermédiaire ou une authentification par utilisateur, pas une clé saisie dans la page).

## 6. Le rendu Git

- Lien de la pull request : https://github.com/Anas-7bx/maintai-g1/pull/10
- Le tag `tp3` existe sur GitHub : oui (tag de groupe `tp3`, sur la fusion de la PR #4)
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? **non** (exclus par `.gitignore` : `.env`, `data/*.csv`, `models/`)

## 7. Ce qui reste flou

…
