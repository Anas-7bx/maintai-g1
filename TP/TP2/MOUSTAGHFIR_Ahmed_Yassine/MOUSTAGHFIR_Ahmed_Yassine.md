# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** G1  ·  **Membres :** MOUSTAGHFIR Ahmed Yassine  ·  **Date :** 11/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| 1 | champ manquant : `load_pct` absent | 422 | 422 |
| 2 | valeur absurde : `load_pct` à 250 (maximum autorisé : 150) | 422 | 422 |
| 3 | texte au lieu d'un nombre : `temperature_c` vaut `"chaud"` | 422 | 422 |
| 4 | champ en trop : `couleur` vaut `"rouge"` (`extra="forbid"`) | 422 | 422 |
| 5 | mauvaise route : `POST /v1/predictt` | 404 | 404 |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

Non. Les quatre premiers cas sont des données invalides : Pydantic les refuse avant le modèle, avec un 422. La cinquième vise une route qui n'existe pas : FastAPI répond 404. Aucune borne de `schemas.py` n'a eu besoin d'être élargie : 250 % de charge est bien au-dessus de 150.

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

Il lance une seule fonction une fois par ligne de `CAS_REFUSES`. pytest compte **5 tests** pour `test_requete_refusee`, un par cas, et il nomme chaque cas dans `python -m pytest -v`.

## 2. ruff

Sortie de `ruff check .` :

```
All checks passed!
```

`ruff format .` a mis 11 fichiers en forme. `python -m pytest` donne ensuite toujours 23 passed.

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

`pytest` exécute le code et vérifie ce qu'il fait (200, 401, 422, le modèle bat la baseline). `ruff` lit le code sans l'exécuter et signale un import inutile, des imports mal rangés, une variable jamais utilisée. Les deux se complètent. Règle du cours : `ruff check .` avant un commit, `python -m pytest` avant un push.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

Tant que `require_api_key` n'est pas branchée sur le router, `test_missing_key_is_rejected` et `test_wrong_key_is_rejected` échouent : l'API répond **200** au lieu de 401. Les autres tests passent, y compris `/health` et les cas de `test_casser.py` qui envoient déjà la clé.

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    attendue = get_settings().api_key
    if attendue is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé API non configurée sur le serveur",
        )
    if x_api_key is None or not secrets.compare_digest(x_api_key.encode(), attendue.encode()):
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

Les deux mêmes. La fonction existe, mais aucune route ne l'appelle : sans clé, la réponse reste 200.

Dernière ligne de `python -m pytest` à la fin du sprint 1 (sans `test_casser.py`) :

```
18 passed, 1 warning in 0.79s
```

Les six requêtes, mesurées sur le modèle entraîné par `python -m maintai.train` (5 000 relevés) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | `{"failure_probability":0.0027,"alert":false,"threshold":0.3,"model_version":"2026-11-11T15:26:01Z"}` |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |

Le relevé normal est `temperature_c` 60, `vibration_mm_s` 2, `load_pct` 50, `runtime_hours` 5000.

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

La clé est vérifiée avant les données. Sans clé, l'API s'arrête au 401 et ne lit pas la température. Avec la bonne clé, le schéma refuse 500 °C : c'est un 422.

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

**500**, avec le détail `Clé API non configurée sur le serveur`. Sans `.env`, `get_settings().api_key` vaut `None`. Le serveur n'est pas configuré : ce n'est pas une clé de client fausse, donc ce n'est pas un 401.

## 5. La page web (sprint 2)

Le bouton envoie `reading` en POST JSON vers `<url>/v1/predict`, avec `Content-Type` et `X-API-Key`. Le résultat passe par `show("ok", ...)`, `show("alert", ...)` ou `show("err", ...)`.

Ce qu'affiche la page pour les valeurs du formulaire (72 °C, vibration 6, charge 85, 15 000 h), mesurées sur le même modèle :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé du formulaire, bonne clé | Probabilité de panne : 94.8 % (ALERTE) |
| 500 °C, bonne clé | Erreur 422, température supérieure à 150 |
| relevé du formulaire, fausse clé | Erreur 401 : Clé API absente ou invalide |

**Expérience CORS.** La page servie sur le port 5501 est une autre origine que `http://localhost:5500`. Le navigateur envoie d'abord OPTIONS. L'API ne renvoie pas `Access-Control-Allow-Origin` pour 5501 (le test `test_cors_refuses_unknown_origin` le vérifie, avec `http://evil.example`). La page affiche alors « API injoignable (arrêtée, ou CORS qui bloque) ». Sur le port 5500, le préflight reçoit `access-control-allow-origin: http://localhost:5500`.

Pourquoi `curl` obtient-il une réponse alors que la page du port 5501 est bloquée ?

CORS est une règle du navigateur. `curl` n'est pas un navigateur : il envoie la requête directement. Avec la bonne clé, il reçoit 200. Seule la clé protège l'API. Le CORS protège l'utilisateur contre une page tierce.

## 6. Les tests de l'activité 1 dans le TP2

Sans `headers=HEADERS`, quatre cas reçoivent **401** au lieu de 422 : valeur absurde, champ manquant, texte, champ en trop. La clé est vérifiée avant les données. Le cas « mauvaise route » reste un **404** : `/v1/predictt` n'existe pas, le contrôle de clé de `/v1` n'est pas appelé.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
23 passed, 1 warning in 0.89s
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   401 : la clé est absente ou fausse, on ne sait pas qui appelle. 422 : l'appelant est accepté, mais le relevé est invalide (500 °C, champ manquant). 403 : on sait qui appelle, mais il n'a pas le droit. Le 403 n'est pas utilisé dans ce TP.
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   Une clé dans le code finit sur GitHub pour toujours, même après un `git rm`. `.env` contient la vraie clé et les origines ; il est ignoré. `.env.example` est commité, avec la fausse valeur `changez-moi` : il dit quoi configurer.
3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   Une URL est écrite dans les journaux du serveur, l'historique du navigateur et l'en-tête Referer. L'en-tête `X-API-Key` ne l'est pas de la même façon.
4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   `==` s'arrête au premier caractère faux. Le temps de réponse dirait alors combien de caractères étaient justes. `compare_digest` compare sans s'arrêter plus tôt.
5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   Une origine, c'est un schéma, un domaine et un port. Ces deux adresses ont le même schéma et le même domaine, mais pas le même port : ce sont deux origines. Le navigateur demande donc la permission (OPTIONS) avant que la page appelle l'API.

## 8. Le rendu Git

- Lien de la pull request : pas encore ouverte
- Le tag `tp2` existe sur GitHub : non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  Personne pour l'instant. Le dossier est prêt à être poussé, il n'a pas été poussé.

Chemin prévu, sur le dépôt du groupe, comme le dossier d'Anas : `TP/TP2/MOUSTAGHFIR_Ahmed_Yassine/`.

## 9. Ce qui reste flou

Je vois bien que le 401 passe avant le 422. Je suis moins sûr du moment exact où le navigateur envoie OPTIONS quand la page et l'API sont toutes les deux sur `localhost`, avec seulement le port qui change.
