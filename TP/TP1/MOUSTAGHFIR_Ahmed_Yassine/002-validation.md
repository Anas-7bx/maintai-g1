# ADR 002 : valider les relevés et répondre 503 si le modèle manque

Date : 28/10/2026 · Auteurs : MOUSTAGHFIR Ahmed Yassine (G1)

## Contexte
L'API reçoit un relevé JSON et doit refuser une valeur impossible avant d'appeler le modèle. Elle doit aussi dire clairement quoi faire si `models/model.joblib` n'est pas encore là. Ces deux choix figent le contrat vu par les clients.

## Options étudiées
1. Bornes copiées sur `sensors.csv` (température d'environ 36 à 93 °C, vibration jusqu'à 22 mm/s, charge de 20 à 100 %, heures jusqu'à 20 000). Avantage : tout le jeu d'entraînement passe. Inconvénient : une machine réelle un peu plus chaude, ou un peu plus chargée que l'échantillon, est refusée alors que la mesure est physique.
2. Bornes physiques, plus larges que l'échantillon. Avantage : le schéma décrit ce qu'un moteur peut afficher. Inconvénient : le modèle peut recevoir un point loin de ce qu'il a vu ; la prédiction reste un nombre, pas une garantie.

1. Refuser de démarrer si le modèle manque. Avantage : on ne sert jamais une API muette. Inconvénient : `/health` et `/docs` sont injoignables tant que l'entraînement n'a pas été lancé, et un oubli de fichier bloque tout le processus.
2. Démarrer quand même et répondre 503 sur `/v1/predict`. Avantage : on voit que le service tourne, et le message dit de lancer `python -m maintai.train`. Inconvénient : un client qui n'appelle que `/health` peut croire que la prédiction est prête.

## Décision
Bornes physiques, en `float` :

| Variable | Minimum | Maximum | Pourquoi |
|---|---|---|---|
| `temperature_c` | −40 °C | 150 °C | En dessous, le capteur n'est plus dans une plage d'atelier ; au-dessus, un moteur ne fonctionne pas. |
| `vibration_mm_s` | 0 | 50 | Une vitesse de vibration est positive. 50 mm/s dépasse déjà une machine en très mauvais état, sans coller au maximum du CSV. |
| `load_pct` | 0 | 150 | 0 % : machine à vide. Au-delà de 100 %, une surcharge courte existe ; 150 % est une limite de protection, pas le 100 du fichier. |
| `runtime_hours` | 0 | 100 000 | Le compteur part de zéro et peut dépasser les 20 000 h de l'échantillon. Le type est `float` : 15 000,5 h doit passer. |

Modèle absent : l'API démarre, `/health` renvoie `"model_loaded": false`, et `/v1/predict` répond **503** avec la commande à lancer. Un 500 laisserait croire à un bug du code.

## Conséquences
Une température de 500 °C est refusée en 422 avant `predict()`. `/docs` affiche les bornes et l'exemple du schéma. Il faudra surveiller les relevés proches des bornes : ils sont acceptés, mais le modèle ne les a pas vus à l'entraînement. Le 503 doit rester un message d'action, pas une page d'erreur vide.
