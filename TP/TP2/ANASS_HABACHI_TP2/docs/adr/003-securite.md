# ADR 003 : Clé API dans un en-tête et origines CORS en liste

Date : 04/11/2026 · Auteurs : Anass Habachi

## Contexte
L'API MaintAI ne doit répondre qu'aux programmes autorisés, et une page web servie sur `http://localhost:5500` doit pouvoir l'appeler. Il faut choisir où la clé voyage et quelles origines le navigateur peut utiliser.

## Options étudiées
**Où transmettre la clé**
1. En-tête `X-API-Key` : n'apparaît pas dans l'URL ; facile à lire côté serveur (`Header`).
2. Dans l'URL (`?key=...`) : simple à tester, mais l'URL est enregistrée partout (journaux du serveur, historique du navigateur, en-tête Referer).
3. Dans le corps JSON : mélange authentification et données ; la clé serait vérifiée après la lecture du corps, donc pas avant la validation.

**Quelles origines autoriser**
1. Une liste explicite, lue depuis `.env` (`MAINTAI_CORS_ORIGINS`) : seules les pages connues peuvent appeler l'API depuis un navigateur.
2. `*` : tout site web pourrait appeler l'API depuis le navigateur d'un utilisateur.

## Décision
- La clé voyage dans l'en-tête `X-API-Key`. Elle est lue au démarrage depuis `.env`, jamais dans le code ni dans Git.
- Les origines autorisées sont une liste dans `.env`, par défaut `localhost:5500` et `127.0.0.1:5500`.

## Conséquences
- Option URL écartée : on perdrait la confidentialité de la clé (elle resterait dans les journaux et l'historique). Option corps écartée : on perdrait le contrôle avant la validation des données (401 avant 422).
- Option `*` écartée : on perdrait la protection de l'utilisateur contre une page tierce qui utiliserait son navigateur pour appeler l'API.
- Le CORS ne protège pas l'API elle-même : `curl` ou Java passent sans question CORS, seule la clé compte.
- Changer la clé ou les origines demande de relancer uvicorn (lecture au démarrage). Une clé commitée par erreur doit être changée.
