# ADR 002 : validation des entrées et comportement sans modèle

Date : 11/11/2026 · Auteurs : Moad Bakouch (G1)

## Contexte
L'API MaintAI reçoit des relevés de capteurs envoyés par d'autres programmes (tableau de bord, application mobile, système de l'atelier). Une valeur impossible, comme une température de 500 °C (capteur débranché ou faute de frappe), ne doit pas atteindre le modèle : il renverrait une probabilité qui a l'air sérieuse mais qui n'a aucun sens. Il faut aussi décider quoi faire quand le fichier du modèle est absent au démarrage.

## Décision 1 : les bornes de chaque variable

Les bornes sont **physiques** : ce qu'un moteur industriel réel peut afficher. Elles ne viennent pas du minimum et du maximum de `sensors.csv` (36 à 93 °C, etc.), sinon une machine réelle un peu plus chaude que celles des données serait refusée. Toutes les variables sont des `float` : 15 000,5 heures est une valeur légitime.

| Variable | Min (`ge`) | Max (`le`) | Justification physique |
|---|---|---|---|
| `temperature_c` | −40 | 150 | −40 °C : un moteur à l'arrêt dans un entrepôt non chauffé ou en extérieur l'hiver. 150 °C : au-delà de la classe d'isolation H des bobinages (180 °C au point chaud), la carcasse ne dépasse pas ~150 °C sans destruction du moteur. Une valeur plus haute est une erreur de capteur. |
| `vibration_mm_s` | 0 | 50 | Une vitesse de vibration efficace ne peut pas être négative. Selon l'ISO 10816, au-delà d'environ 11 mm/s la machine est déjà en zone « dommages ». 50 mm/s laisse de la marge pour une machine en train de casser tout en écartant les valeurs aberrantes. |
| `load_pct` | 0 | 120 | 0 % : la machine tourne à vide. Un moteur peut fonctionner brièvement en **surcharge** (facteur de service de 1,15 à 1,2), donc jusqu'à ~120 % de la charge nominale. Une machine en surcharge est justement une machine à risque : il ne faut pas la refuser. Au-delà, c'est une erreur. |
| `runtime_hours` | 0 | 200 000 | Un compteur d'heures ne peut pas être négatif. 200 000 h, c'est environ 23 ans de fonctionnement 24 h/24, la durée de vie maximale réaliste d'une machine industrielle. |

## Décision 2 : modèle absent, répondre 503 ou refuser de démarrer ?

### Options étudiées
1. **Démarrer quand même et répondre 503 sur `/v1/predict`** (et `model_loaded: false` sur `/health`).
   - Avantages : l'API reste joignable. `/health` dit clairement ce qui ne va pas, `/docs` reste consultable, et un orchestrateur ou un humain peut diagnostiquer sans lire les journaux du serveur. Dès qu'un modèle est entraîné, un simple redémarrage suffit.
   - Inconvénients : une API « en marche » qui ne sait rien faire. Un client qui ne regarde que la connexion croit que tout va bien ; il faut surveiller `/health`.
2. **Refuser de démarrer** (le processus s'arrête avec une erreur).
   - Avantages : l'échec est immédiat et impossible à ignorer, et on ne déploie jamais une API inutile.
   - Inconvénients : plus de `/health` ni de `/docs`, et le client ne reçoit qu'une erreur de connexion, sans explication. Dans un environnement qui relance automatiquement les services, le service redémarre en boucle.

### Décision
**Option 1 : démarrer et répondre 503 Service Unavailable**, avec un message qui dit quoi faire (« lancez python -m maintai.train puis redémarrez l'API »). 503 est le bon code : le client n'a rien fait de mal (ce n'est pas un 4xx), et le serveur n'a pas planté (ce n'est pas un 500). Le service est **temporairement** indisponible, et la requête réussira une fois le modèle chargé.

## Conséquences
- Les clients doivent traiter le 503 (afficher « service indisponible », réessayer plus tard). La supervision doit lire `model_loaded` dans `/health`, et pas seulement vérifier que le port répond.
- La validation par Pydantic renvoie un **422** qui dit quel champ est faux et pourquoi, avant d'appeler le modèle. Le code de `predict()` ne voit jamais de valeur impossible.
- Les bornes sont à **revoir avec les données réelles** de l'usine, par exemple si certains moteurs dépassent 120 % de charge ou si les capteurs mesurent autre chose.
- `extra="forbid"` refuse les champs inconnus. Une faute de frappe dans un nom de champ (`temprature_c`) est détectée au lieu d'être ignorée en silence. En contrepartie, ajouter une variable au modèle demandera une nouvelle version du contrat (`/v2`).
