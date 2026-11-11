# Compte rendu · TP3 : une interface Streamlit pour MaintAI

**ANASS HABACHI  G1**   ·  **Date :** 11/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP3.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP3`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
================= 5 failed, 18 passed, 1 warning in 6.40s ==================
```

Quels fichiers de tests échouent, et quelle erreur donnent-ils ?

Deux fichiers échouent :
- `tests/test_client.py` (3 tests) : `NotImplementedError: TP3 sprint 2 : MaintaiClient.predict`. La méthode `predict` du client n'est pas encore écrite.
- `tests/test_ui.py` (2 tests) : `IndexError: list index out of range`. Les tests cherchent un `st.metric` (`at.metric[0]`, `at.metric[-1]`), mais la page n'en affiche aucun : le code des onglets n'est pas écrit.

## 2. Lancer Streamlit

Lancez d'abord `streamlit run ui/app.py`. Que s'affiche-t-il dans le navigateur ?

```
ModuleNotFoundError: No module named 'maintai'
File "C:\Users\DELL\Downloads\maintai-starter-tp3\ui\app.py", line 9, in <module>
    from maintai.client import APIError, MaintaiClient
```

Lancez ensuite `python -m streamlit run ui/app.py`. Pourquoi cette commande fonctionne-t-elle et pas la première ?

Avec cette seconde commande, la page s'affiche (titre « MaintAI », barre latérale, deux onglets). Python cherche les modules dans une liste de dossiers (`sys.path`). Avec `streamlit run ui/app.py`, cette liste contient le dossier du script (`ui/`), mais pas la racine du projet : `maintai` est donc introuvable. Avec `python -m streamlit`, Python ajoute le dossier courant (la racine du projet) à la liste, donc `import maintai` fonctionne.

## 3. Sprint 1 : l'onglet « Données »

Votre code de l'onglet « Données » (de `c1, c2, c3 = ...` jusqu'au nuage de points) :

```python
c1, c2, c3 = st.columns(3)
c1.metric("Relevés", len(df))
c2.metric("Taux de panne", f"{df.failure.mean():.1%}")
c3.metric("Température moyenne", f"{df.temperature_c.mean():.1f} °C")

variable = st.selectbox("Variable", FEATURES)
tranches = pd.cut(df[variable], bins=10)
taux = df.groupby(tranches, observed=True).failure.mean()
taux.index = [round(i.mid, 1) for i in taux.index]
st.bar_chart(taux)

df_nuage = df.assign(panne=df.failure.map({0: "non", 1: "oui"}))
st.scatter_chart(df_nuage, x="temperature_c", y="vibration_mm_s", color="panne")
```

| Indicateur | Valeur affichée |
|---|---|
| Relevés | 5000 |
| Taux de panne | 13.6 % |
| Température moyenne | 59.8 °C |

Choisissez `vibration_mm_s` dans la liste. Comment évolue le taux de panne quand la vibration augmente ?

Le taux de panne augmente fortement avec la vibration. Il est d'environ 2 % pour les vibrations les plus faibles, passe à 10 %, 32 %, 66 % et 84 % pour les tranches suivantes, puis atteint 100 % pour les vibrations les plus élevées (8 barres seulement : deux des 10 tranches ne contiennent aucun relevé et disparaissent grâce à `observed=True`). C'est la variable la plus déterminante : à titre de comparaison, le taux de panne par tranche de température monte seulement jusqu'à environ 37 %, celui de la charge jusqu'à 25 % et celui des heures de fonctionnement jusqu'à 19 %.

Ajoutez un `print("relance")` en haut de `ui/app.py`, puis déplacez un curseur. Que voyez-vous dans le terminal, et qu'est-ce que cela montre sur le fonctionnement de Streamlit ?

« relance » s'affiche dans le terminal au premier affichage de la page, puis une nouvelle fois à chaque interaction avec un widget (par exemple quand on choisit `vibration_mm_s` dans la liste). Cela montre que Streamlit réexécute tout le script `ui/app.py`, de la première à la dernière ligne, à chaque interaction, avec les nouvelles valeurs des widgets. Les curseurs du formulaire de l'onglet « Prédiction » sont une exception : ils ne relancent rien, seul le bouton « Prédire » relance le script.

À quoi sert `@st.cache_data` sur la fonction `charger` ?

Streamlit réexécute tout le script à chaque interaction. Sans `@st.cache_data`, le fichier CSV serait relu à chaque clic. Avec le cache, la fonction n'est exécutée qu'une fois pour un même argument et le résultat est réutilisé aux relances suivantes, ce qui rend la page plus rapide.

## 4. Sprint 2 : l'onglet « Prédiction »

Votre méthode `predict` (`maintai/client.py`) :

```python
def predict(self, reading: dict) -> dict:
    headers = {"X-API-Key": self.api_key} if self.api_key else {}
    r = self.http.post("/v1/predict", json=reading, headers=headers)
    if r.status_code != 200:
        raise APIError(r.status_code, r.json().get("detail"))
    return r.json()
```

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
23 passed, 1 warning in 4.65s
```

Avec l'API lancée (`uvicorn maintai.api.main:app --reload --env-file .env`) :

| Essai | Ce qu'affiche Streamlit |
|---|---|
| valeurs par défaut, bonne clé | Probabilité de panne : 95 %, avec l'alerte rouge « ALERTE : risque de panne, prévoir une intervention. » |
| valeurs par défaut, fausse clé | Avertissement jaune : « L'API a refusé le relevé (code 401) : Clé API absente ou invalide » |
| API arrêtée (Ctrl+C dans le terminal d'uvicorn) | Erreur rouge : « API injoignable (http://localhost:8000). Vérifiez qu'uvicorn tourne et que l'URL est correcte. » |

Le port 8501 n'est pas dans `MAINTAI_CORS_ORIGINS`, et pourtant la prédiction fonctionne. Pourquoi ?

CORS est une protection appliquée par le navigateur : il bloque une page JavaScript qui appelle une API d'une autre origine, sauf si l'API l'autorise. Dans Streamlit, ce n'est pas le navigateur qui appelle l'API : c'est le serveur Streamlit (du code Python, via `httpx`) qui envoie la requête. Le navigateur ne parle qu'à Streamlit, il n'y a donc aucune requête inter-origines à contrôler, et CORS n'intervient pas.

## 5. Questions de compréhension

1. Dans la page web du TP2, qui envoie la requête à l'API ? Et dans Streamlit ?
   Dans la page web du TP2, c'est le navigateur de l'utilisateur, avec `fetch` en JavaScript. Dans Streamlit, c'est le serveur Streamlit, avec le client Python (`MaintaiClient`, basé sur `httpx`).
2. Pourquoi les tests de `test_client.py` n'ont-ils pas besoin d'uvicorn ?
   `MaintaiClient` reçoit un client HTTP par le paramètre `http=`. Les tests lui donnent le `TestClient` de FastAPI, qui envoie la requête directement à l'application en mémoire, sans réseau ni serveur. Le code de `predict` est le même.
3. Page HTML + JavaScript (TP2) ou Streamlit (TP3) : laquelle choisiriez-vous pour une démonstration à un client ? Et pour l'application d'un technicien de maintenance ? Pourquoi ?
   Pour une démonstration à un client, la page HTML + JavaScript : l'interface est entièrement personnalisable et peut avoir l'image de l'entreprise. Pour l'application d'un technicien, Streamlit : le développement est rapide, tout est en Python, et un technicien a besoin d'une interface simple et fonctionnelle plus que d'un design soigné.

## 6. Le rendu Git

- Lien de la pull request : https://github.com/Anas-7bx/maintai-g1/pull/4 (branche `tp3-anass`, dossier `TP/TP3/ANASS_HABACHI_TP3`)
- Le tag `tp3` existe sur GitHub : non, pas encore (il se pose après la fusion de la pull request)
- `git status` avant le commit : `.env`, `data/` ou `models/` apparaissaient-ils ? **non** : seuls `ui/app.py`, `maintai/client.py` et `COMPTE_RENDU.md` ont été ajoutés au dépôt

## 7. Ce qui reste flou

**Mon avis :** ce TP m'a montré qu'une interface complète peut s'écrire entièrement en Python, sans HTML ni JavaScript. Le point le plus important pour moi : avec Streamlit, c'est le serveur Python qui appelle l'API, pas le navigateur. C'est pour cela que CORS ne bloque rien ici, alors que la clé API reste obligatoire (401 avec une fausse clé).

**Ce qui reste un peu flou pour moi :**
- La relance du script à chaque clic : je l'ai vue avec `print("relance")`, mais je ne sais pas encore jusqu'où cela reste rapide quand les données sont plus grosses que 5000 lignes, même avec `@st.cache_data`.
- Le fonctionnement exact de `st.form` : je comprends que les curseurs du formulaire ne relancent rien avant le bouton « Prédire », mais je ne sais pas encore comment garder le résultat affiché après un autre clic.

**Les difficultés que j'ai rencontrées :**
1. **`streamlit run ui/app.py` ne trouvait pas `maintai`** (`ModuleNotFoundError`). Il faut lancer `python -m streamlit run ui/app.py` depuis la racine du projet.
2. **Le fichier `.env` du TP2 était introuvable** : le zip avait été extrait dans un sous-dossier (`S5_maintai-starter-tp2\maintai-starter-tp2`). Il a fallu le retrouver pour le copier dans le TP3.
3. **Une erreur d'indentation** dans l'onglet « Données » : une ligne écrite sans les 4 espaces sortait du bloc `with onglet_donnees:`.
