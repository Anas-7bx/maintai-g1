# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** G1  ·  **Membres :** Anass Habachi  ·  **Date :** 04/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| 1 | champ manquant : `load_pct` absent | 422 | 422 |
| 2 | valeur absurde : `load_pct: 250` (maximum autorisé : 150) | 422 | 422 |
| 3 | texte au lieu d'un nombre : `temperature_c: "chaud"` | 422 | 422 |
| 4 | champ en trop : `couleur: "rouge"` (refusé par `extra="forbid"`) | 422 | 422 |
| 5 | mauvaise route : `POST /v1/predictt` | 404 | 404 |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

Non, aucune : les cinq codes obtenus sont ceux que nous avions prévus. Les quatre premières requêtes sont des données invalides : Pydantic les refuse avant d'appeler le modèle, avec un 422 (« Unprocessable Entity »). La cinquième vise une route qui n'existe pas : FastAPI répond 404, car la route est cherchée avant que les données ne soient lues. Aucune borne de `schemas.py` n'a donc eu besoin d'être corrigée.

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
19 passed, 1 warning in 5.18s
```

(13 tests fournis + 5 cas de `test_casser.py` + 1 test de `test_client.py` écrit au préalable. Le warning est un avertissement de dépréciation de `httpx` dans Starlette, sans lien avec notre code.)

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

`@pytest.mark.parametrize` permet d'écrire une seule fonction de test et de la faire exécuter plusieurs fois, une fois par ligne de la liste `CAS_REFUSES`, avec des paramètres différents (description, URL, corps, code attendu). On évite de recopier cinq fois le même test. pytest compte **5 tests** pour la fonction `test_requete_refusee`, un par cas, et chaque cas est nommé dans le rapport (`python -m pytest -v`) : si l'un échoue, on sait lequel, sans que les autres soient arrêtés.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
All checks passed!
```

(`ruff format .` a ensuite mis en forme le code : 20 fichiers formatés ; `python -m pytest` donne toujours 19 passed.)

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

`python -m pytest` **exécute** le code et vérifie ce qu'il fait : un relevé valide donne 200, 500 °C donne 422, le modèle bat la baseline. `ruff check .` **lit** le code sans l'exécuter et vérifie comment il est écrit : import inutile (F401), imports mal rangés (I001), variable jamais utilisée. Du code peut passer tous les tests et avoir des problèmes de qualité, et inversement du code propre peut être faux : les deux sont complémentaires. La règle : `ruff check .` avant chaque commit, `python -m pytest` avant chaque push.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
2 failed, 16 passed, 1 warning in 8.15s
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

Les deux tests de `tests/test_security.py` échouent :
- `test_missing_key_is_rejected` : requête **sans clé** ;
- `test_wrong_key_is_rejected` : requête avec une **fausse clé**.

Dans les deux cas l'API répond **200 OK** (`assert 200 == 401`) au lieu de 401 : la clé n'est pas encore vérifiée, donc l'API accepte tout le monde. Les 16 autres tests passent, dont les 5 cas de `test_casser.py` (qui envoient `headers=HEADERS`).

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    expected = get_settings().api_key
    if expected is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé API non configurée sur le serveur",
        )
    if x_api_key is None or not secrets.compare_digest(
        x_api_key.encode(), expected.encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
```

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

Toujours 2 : la fonction existe, mais aucune route ne l'appelle encore, donc l'API répond toujours 200 sans clé.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
18 passed, 1 warning in 2.51s
```

Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl.exe`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | `{"failure_probability":0.0027,"alert":false,"threshold":0.3,...}` |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | erreur de validation Pydantic (température hors bornes) |

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

La clé est vérifiée avant les données : sans clé, l'API refuse tout de suite (401) sans regarder le corps. Avec la bonne clé, la requête passe le contrôle d'authentification, puis le schéma refuse 500 °C (422).

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

500 (« Clé API non configurée sur le serveur »). Sans `.env` chargé, `get_settings().api_key` vaut `None` : le problème vient de la configuration du serveur, pas de la clé du client, donc ce n'est pas un 401.

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
  const adresse = document.getElementById("url").value.replace(/\/$/, "") + "/v1/predict";
  const cle = document.getElementById("key").value;
  try {
    const resp = await fetch(adresse, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": cle },
      body: JSON.stringify(reading),
    });
    const data = await resp.json();
    if (!resp.ok) {
      show("err", `Erreur ${resp.status} : ${JSON.stringify(data.detail)}`);
    } else {
      const p = (data.failure_probability * 100).toFixed(1);
      show(data.alert ? "alert" : "ok", `Probabilité de panne : ${p} %` + (data.alert ? " (ALERTE)" : ""));
    }
  } catch (e) {
    show("err", "API injoignable (arrêtée, ou CORS qui bloque)");
  }
```

Ce qu'affiche la page (servie sur le port 5500) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | « Probabilité de panne : 94.8 % (ALERTE) » (fond rouge) |
| 500 °C, bonne clé | « Erreur 422 : » suivi du détail de validation (fond orange) |
| relevé normal, fausse clé | « Erreur 401 : "Clé API absente ou invalide" » (fond orange) |

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

La page affiche « API injoignable (arrêtée, ou CORS qui bloque) ». La console indique que la requête vers `http://localhost:8000` depuis l'origine `http://localhost:5501` est bloquée par la politique CORS : pas d'en-tête `Access-Control-Allow-Origin`. Vérifié avec `curl.exe -X OPTIONS` : origine 5500 → `200` avec `access-control-allow-origin: http://localhost:5500` ; origine 5501 → `400 Bad Request`, sans cet en-tête (« Disallowed CORS origin »).

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

CORS est une règle du **navigateur** : il protège l'utilisateur contre une page qui utiliserait son navigateur pour appeler l'API. `curl.exe` n'est pas un navigateur, il n'applique pas cette règle (essai : `POST` avec la bonne clé → 200). Ce n'est donc pas une protection de l'API : seule la clé compte.

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

4 tests échouent : valeur absurde, champ manquant, texte au lieu d'un nombre, champ en trop. Ils reçoivent **401** au lieu de 422, car la clé est vérifiée avant les données. Le cas « mauvaise route » passe quand même (404) : la route `/v1/predictt` n'existe pas, donc FastAPI répond 404 avant tout contrôle de clé.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
23 passed, 1 warning in 2.54s
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   401 : l'API ne sait pas qui appelle (clé absente ou fausse). 422 : l'appelant est accepté mais ses données sont invalides. 403 : on sait qui appelle, mais il n'a pas le droit (autorisation), alors que 401 concerne l'authentification.
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   Une clé commitée reste dans l'historique de Git pour toujours, même si on supprime le fichier. `.env` contient la vraie clé et n'est pas commité (ignoré par `.gitignore`) ; `.env.example` contient une fausse valeur et dit quoi configurer : c'est lui qui est commité.
3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   Une URL est enregistrée partout (journaux du serveur, historique du navigateur) ; un en-tête n'y apparaît pas.
4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   Il compare en temps constant : `==` s'arrête au premier caractère faux, et la durée de la réponse révélerait combien de caractères étaient justes.
5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   Une origine = schéma + domaine + port. Non, ce sont deux origines différentes (le port change), d'où le CORS.

## 8. Le rendu Git

- Lien de la pull request : …
- Le tag `tp2` existe sur GitHub : oui / non
- `git status` avant le commit : le fichier `.env` apparaissait-il ? oui / non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  …

## 9. Ce qui reste flou

**Mon avis :** ce TP m'a montré qu'une API sans clé laisse entrer tout le monde. Avec la clé dans l'en-tête, l'API refuse les inconnus (401) avant même de regarder les données. J'ai aussi compris que le CORS protège seulement le navigateur : `curl` passe quand même, donc la clé reste le vrai verrou.

**Ce qui reste un peu flou pour moi :**
- La différence entre 401 et 403 : je la comprends, mais je ne l'ai pas essayée (le 403 n'est pas dans ce TP).
- Comment on garde la clé en sécurité en production (ce sera la séance 8).

**Les difficultés que j'ai rencontrées :**
1. **Mauvais serveur sur le port 8000.** Le serveur du TP1 (sans clé) tournait encore. Il répondait 200 même sans clé, et la page affichait « API injoignable ». Il a fallu l'arrêter avant de lancer celui du TP2.
2. **Environnement Python.** Le Python global n'avait ni pytest ni ruff. J'ai dû créer un `.venv` et installer `requirements.txt`.
3. **Lancer uvicorn avec `--env-file .env`.** Sans cette option, la clé n'est pas lue et l'API répond 500 au lieu de 401.
4. **Le piège de `ruff --fix` dans le TP2.** Avant d'avoir écrit le code, il aurait supprimé les imports `Depends` et `secrets`. Je l'ai lancé seulement à la fin du sprint 1.
5. **Comprendre le CORS.** Il m'a fallu l'expérience du port 5501 pour voir la différence entre « le navigateur bloque » et « l'API refuse ».
6. **L'ordre des contrôles.** Au début, je ne voyais pas pourquoi 500 °C sans clé donne 401 et pas 422 : la clé est vérifiée avant les données.
