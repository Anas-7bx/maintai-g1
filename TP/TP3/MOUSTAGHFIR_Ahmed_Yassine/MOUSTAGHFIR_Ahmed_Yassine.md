# Compte rendu · TP3 : une interface Streamlit

**Groupe :** G1  ·  **Membres :** MOUSTAGHFIR Ahmed Yassine  ·  **Date :** 11/11/2026

## 1. Les deux façons de lancer la page

Les deux commandes ouvrent la même page, http://localhost:8501. Le serveur répond 200. Aucune demande d'e-mail : `.streamlit/config.toml` coupe la collecte d'usage.

```text
streamlit run ui/app.py
python -m streamlit run ui/app.py
```

Les deux affichent « You can now view your Streamlit app in your browser » et « Local URL: http://localhost:8501 ».

## 2. Onglet Données

Trois indicateurs : le nombre de relevés, le taux de panne, la température moyenne. Le premier est le nombre de relevés. Une liste propose les quatre variables de `FEATURES`. Les barres montrent le taux de panne par tranche. Le nuage place la température en abscisse et la vibration en ordonnée, coloré « oui / non ».

Jeu généré par `python -m maintai.dataset` : 5 000 relevés, taux de panne 13,6 %. Pour `vibration_mm_s`, le taux monte avec la vibration :

| Milieu de tranche (mm/s) | Taux de panne |
|---|---|
| 1,1 | 2,0 % |
| 3,4 | 9,8 % |
| 5,6 | 32,3 % |
| 7,8 | 66,4 % |
| 10,0 | 83,6 % |
| 12,2 et au-dessus | 100 % |

La vibration sépare le plus les pannes : le taux va de 2 % à 100 % (écart 98 points). La température va de 0 % à 37 %, la charge de 5 % à 25 %, les heures de 8 % à 19 %.

## 3. Onglet Prédiction

Valeurs du formulaire : 72 °C, vibration 6, charge 85, 15 000 h. Mesure sur le modèle de `python -m maintai.train` (accuracy 0,904, recall 0,75, precision 0,622, seuil 0,3). L'API a répondu `failure_probability` 0,9475, `alert` true, version `2026-11-11T15:44:10Z`.

| Essai | Ce qui s'affiche |
|---|---|
| valeurs par défaut, bonne clé | Probabilité de panne : 95 % (ALERTE) |
| valeurs par défaut, fausse clé | Erreur 401 : Clé API absente ou invalide |
| API arrêtée | API injoignable (arrêtée, ou mauvaise URL) |

Le dernier cas est un `ConnectError` de httpx : rien n'écoute sur le port.

## 4. Pourquoi pas de CORS ?

En TP2, le navigateur appelait l'API depuis une autre origine, et le port 5501 était bloqué. Ici, le navigateur ne parle qu'à Streamlit (port 8501). C'est le processus Python qui appelle l'API avec httpx. CORS est une règle du navigateur. httpx n'est pas un navigateur : le port 8501 n'a pas besoin d'être dans `MAINTAI_CORS_ORIGINS`.

## 5. Tests

```text
23 passed, 1 warning in 1.62s
```

`ruff check .` : All checks passed.

Les cinq tests ajoutés par rapport au TP2 (sans `test_casser.py`, qui en faisait 18) sont les trois de `tests/test_client.py` et les deux de `tests/test_ui.py`. Le client utilise `self.http.post`, pas `httpx.post`. La page est exécutée par `AppTest`, sans navigateur.

## 6. Rendu Git

Pas de pull request, pas de tag `tp3`. Le dossier est prêt à être poussé, il n'a pas été poussé.

Chemin prévu : `TP/TP3/MOUSTAGHFIR_Ahmed_Yassine/`.

## 7. Ce qui reste flou

Je vois que les curseurs d'un formulaire ne relancent rien tant qu'on n'a pas cliqué sur « Prédire ». Je suis moins sûr de ce que Streamlit garde en mémoire quand deux personnes ouvrent la même page en même temps.
