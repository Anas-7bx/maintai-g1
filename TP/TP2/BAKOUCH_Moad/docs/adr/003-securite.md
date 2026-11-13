# ADR 003 : transmission de la clé API et origines autorisées (CORS)

Date : 11/11/2026 · Auteurs : Moad Bakouch (G1)

## Contexte
L'API MaintAI ne doit répondre qu'aux programmes autorisés, qui prouvent leur identité par une clé. Cette clé ne doit jamais apparaître dans le code ni dans Git. Par ailleurs, une page web servie sur `http://localhost:5500` doit pouvoir appeler l'API depuis un navigateur, mais pas une page servie ailleurs. Il faut donc décider **où voyage la clé** et **quelles origines le navigateur a le droit d'utiliser**.

## Décision 1 : où transmettre la clé ?

### Options étudiées
1. **Dans l'URL** (`/v1/predict?api_key=...`).
   - Avantages : rien à configurer côté client, on peut tester dans la barre d'adresse.
   - Inconvénients : une URL est **enregistrée partout**, dans les journaux du serveur, des proxys et des pare-feux, l'historique et les favoris du navigateur, l'en-tête `Referer` envoyé à d'autres sites, les captures d'écran. La clé fuit sans que personne ne s'en rende compte.
2. **Dans le corps JSON** (`{"api_key": ..., "temperature_c": ...}`).
   - Avantages : pas dans les journaux d'URL.
   - Inconvénients : le secret est mélangé aux données métier et casse le contrat d'entrée (`extra="forbid"` le refuserait). Il ne marche pas pour un `GET`, qui n'a pas de corps, et il faudrait répéter le contrôle dans chaque schéma, sans pouvoir le factoriser en dépendance.
3. **Dans un en-tête HTTP `X-API-Key`.**
   - Avantages : les en-têtes ne sont pas journalisés par défaut et ne vont pas dans l'historique. L'authentification est séparée des données, et le contrôle est factorisé en une seule dépendance FastAPI (`Depends(require_api_key)`) sur tout le router `/v1`. `/docs` l'affiche comme un champ à part.
   - Inconvénients : il faut ajouter un en-tête côté client (`-H` avec curl, `headers` avec fetch), et l'en-tête doit être autorisé dans CORS (`allow_headers`).

### Décision
**L'en-tête `X-API-Key`**, comparé avec `secrets.compare_digest`, dont la durée de comparaison est constante, pour ne pas indiquer combien de caractères sont justes. La clé attendue est lue au démarrage dans la variable d'environnement `MAINTAI_API_KEY`, chargée depuis `.env` (`--env-file .env`). `.env` est dans `.gitignore`, et seul `.env.example`, avec une fausse valeur, est commité. Clé absente ou fausse : **401**. Serveur sans clé configurée : **500**, car c'est une erreur de configuration du serveur et pas du client.

Ce que l'option URL ferait perdre : la confidentialité de la clé, qui finirait dans les journaux. Ce que l'option corps ferait perdre : la séparation entre authentification et données, et un contrôle unique pour toutes les routes.

## Décision 2 : quelles origines autoriser ?

### Options étudiées
1. **`allow_origins=["*"]`**, toutes les origines.
   - Avantages : aucune configuration, n'importe quelle page peut appeler l'API.
   - Inconvénients : n'importe quel site web visité par un utilisateur peut appeler l'API depuis son navigateur. Si la clé est saisie dans une page ou stockée par le navigateur, un site malveillant peut s'en servir. On perd tout contrôle sur qui intègre l'API dans une page.
2. **Une liste explicite d'origines**, lue dans `.env` (`MAINTAI_CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500`).
   - Avantages : seules les pages connues peuvent appeler l'API depuis un navigateur. La liste change par environnement (développement, production) **sans modifier le code**.
   - Inconvénients : il faut ajouter chaque nouvelle origine, puis redémarrer uvicorn (la liste est lue au démarrage). Une page servie sur un autre port (5501) est bloquée, ce qui est voulu mais peut surprendre.
3. **Une liste écrite en dur dans le code.**
   - Inconvénients : il faut modifier le code et redéployer pour chaque environnement.

### Décision
**Une liste explicite, configurée dans `.env`** (option 2), avec seulement les méthodes `GET` et `POST` et les en-têtes `Content-Type` et `X-API-Key`. Valeur par défaut dans `config.py` : `http://localhost:5500` et `http://127.0.0.1:5500`.

Ce que `*` ferait perdre : la garantie que seules nos pages appellent l'API depuis un navigateur. Ce qu'une liste en dur ferait perdre : la possibilité de configurer chaque environnement sans toucher au code.

## Conséquences
- CORS n'est **pas** une authentification : c'est le **navigateur** qui l'applique. `curl.exe`, Python (httpx, Streamlit) ou Java ignorent CORS. Seule la clé protège vraiment l'API ; CORS limite seulement les pages web qui peuvent l'utiliser depuis un navigateur.
- La clé envoyée à une page web reste visible par l'utilisateur de cette page (outils F12). Pour une vraie application publique, il faudrait un serveur intermédiaire ou une authentification par utilisateur (OAuth2) avec des droits (403).
- Sur HTTP en clair, l'en-tête circule en clair : en production, **HTTPS est obligatoire**.
- Une clé poussée par erreur sur Git reste dans l'historique : il faut alors la **changer**, et pas seulement supprimer le fichier.
- Ordre des contrôles : CORS (navigateur), puis route (404), puis clé (401), puis validation (422), puis modèle (503). 500 °C sans clé donne donc 401, pas 422.
