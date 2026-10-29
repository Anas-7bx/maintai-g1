# ADR 002 : validation des entrées de l'API et comportement sans modèle

Date : 28/10/2026 · Auteurs : Anass Habachi (G1)

## Contexte
L'API MaintAI reçoit des relevés de capteurs envoyés par d'autres programmes (tableau de bord, application mobile, système de l'atelier). Une valeur impossible (capteur défaillant, faute de saisie) ne doit jamais atteindre le modèle, et l'API doit réagir clairement si le modèle entraîné est absent.

Deux décisions sont à prendre : les bornes acceptées pour chaque variable, et le comportement de l'API quand `models/model.joblib` n'existe pas.

## Décision 1 : les bornes de chaque variable

### Options étudiées
1. **Bornes copiées sur les données** (min et max de `sensors.csv`) : faciles à calculer, mais trop étroites. Une machine réelle un peu plus chaude ou plus usée que celles de l'échantillon serait refusée, alors que sa mesure est parfaitement possible.
2. **Bornes physiques** (ce qu'un moteur réel peut afficher) : demandent de réfléchir à chaque grandeur, mais ne refusent que les valeurs réellement impossibles.

### Décision
Bornes physiques, toutes en `float` (un `int` refuserait par exemple 15000,5 heures) :

| Variable | Bornes | Justification |
|---|---|---|
| `temperature_c` | -40 à 150 °C | -40 °C : moteur à l'arrêt dans un local non chauffé en hiver. 150 °C : limite d'isolation des bobinages (classe F, 155 °C) ; au-delà, le moteur est détruit. |
| `vibration_mm_s` | 0 à 100 mm/s | Une vitesse de vibration efficace est positive. ISO 10816 classe une machine « dangereuse » dès environ 11 à 45 mm/s ; 100 mm/s laisse une marge sans accepter de valeur absurde. |
| `load_pct` | 0 à 150 % | 0 % : moteur à vide. Une surcharge brève au-dessus de 100 % est possible (démarrage) ; au-delà de 150 %, les protections coupent le moteur. |
| `runtime_hours` | 0 à 200 000 h | Un compteur d'heures n'est pas négatif. 200 000 h ≈ 23 ans en marche continue, la durée de vie d'un moteur industriel. |

### Conséquences
- Une valeur impossible est refusée avec un **422** qui indique le champ et la borne ; le modèle n'est jamais appelé.
- Une valeur possible mais rare (hors de la plage d'entraînement) est acceptée : le modèle extrapole. Il faudra surveiller ces cas (dérive des données, séances suivantes).
- Les bornes apparaissent automatiquement dans `/docs`.

## Décision 2 : modèle absent, répondre 503 ou refuser de démarrer ?

### Options étudiées
1. **Démarrer quand même et répondre 503 sur `/v1/predict`** :
   - on garde : `/health` répond (avec `"model_loaded": false`), `/docs` reste consultable, l'outil de supervision voit que le service est en vie mais pas prêt ;
   - on perd : une API « à moitié prête » peut passer inaperçue si personne ne regarde `/health` ; les clients reçoivent des erreurs au lieu d'un échec visible au déploiement.
2. **Refuser de démarrer** (planter au lancement) :
   - on garde : impossible de mettre en service une API sans modèle, le problème est vu tout de suite au déploiement ;
   - on perd : plus aucune réponse, même `/health` ni `/docs` ; le client ne reçoit qu'une connexion refusée, sans message expliquant quoi faire ; diagnostic plus difficile à distance.

### Décision
**Démarrer et répondre 503**, avec un message qui dit quoi faire (« lancez `python -m maintai.train`, puis redémarrez l'API »). Le code 503 (« service indisponible ») est juste : le code n'a pas de bug (ce serait un 500), c'est une ressource qui manque. Le client sait qu'il peut réessayer, et l'équipe sait quoi corriger.

### Conséquences
- `/health` doit être surveillé : `"model_loaded": false` signale le problème.
- Le modèle est chargé une seule fois, au démarrage : après un nouvel entraînement, il faut **redémarrer** l'API pour qu'elle le prenne en compte.
