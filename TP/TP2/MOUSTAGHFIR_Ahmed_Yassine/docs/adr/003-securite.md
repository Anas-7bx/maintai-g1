# ADR 003 : clé dans un en-tête, origines en liste

Date : 11/11/2026 · Auteurs : MOUSTAGHFIR Ahmed Yassine

## Contexte
L'API MaintAI ne doit répondre qu'aux programmes autorisés. Une page servie sur `http://localhost:5500` doit pouvoir l'appeler. Une page servie ailleurs, non. La clé ne doit pas finir dans Git.

## Options étudiées
Où transmettre la clé :

1. En-tête `X-API-Key`. Elle n'est pas dans l'adresse. Le serveur la lit avant le corps.
2. Dans l'URL (`?cle=...`). Simple à coller, mais l'adresse est écrite dans les journaux, l'historique du navigateur et l'en-tête Referer.
3. Dans le corps JSON. La clé se mélange aux capteurs, et elle n'est lue qu'après le début de la validation.

Quelles origines autoriser :

1. Une liste, lue dans `.env` (`MAINTAI_CORS_ORIGINS`). Seules les pages prévues passent le contrôle du navigateur.
2. `*`. N'importe quel site pourrait appeler l'API depuis le navigateur d'un visiteur.

## Décision
La clé voyage dans l'en-tête `X-API-Key`. Elle est lue au démarrage depuis `.env` (`MAINTAI_API_KEY`), jamais écrite dans le code. Les origines autorisées sont la liste de `.env`, par défaut `http://localhost:5500` et `http://127.0.0.1:5500`.

## Conséquences
Mettre la clé dans l'URL la laisserait dans les journaux. La mettre dans le corps empêcherait de répondre 401 avant le 422 des données. Autoriser `*` ouvrirait l'API à n'importe quelle page web. Le CORS ne remplace pas la clé : `curl` et un programme Java ne posent pas la question OPTIONS, seule la clé les arrête. Changer `.env` demande de relancer uvicorn. Une clé déjà poussée doit être changée.
