# Choix du modèle

Date : 11/11/2026 · Groupe : G1 (Anass Habachi, Adnane Habbaz, Ahmed Yassine Moustaghfir, Moad Bakouch)

## Contexte
MaintAI prédit, pour chaque relevé de capteurs, si la machine va tomber en panne (classification binaire). Une panne manquée arrête une ligne de production une journée ; une fausse alerte coûte une heure d'inspection. La **métrique principale est donc le rappel** (la part des vraies pannes détectées) ; la précision sert de garde-fou contre les fausses alertes (section 5 de l'étude de conception).

## Données et découpage
- Fichier : `data/exemple_pannes.csv` (non versionné), 5 000 relevés synthétiques, 17,6 % de pannes, aucune donnée personnelle.
- Variables : `temperature_c`, `vibration_mm_s`, `load_pct`, `runtime_hours` ; cible `failure`.
- Découpage **aléatoire stratifié**, 20 % en test (1 000 relevés, ≈ 176 pannes), graine 42. Le jeu de test sert uniquement à la mesure finale, le même pour tous les modèles.

## Résultats sur le jeu de test

Sortie de `python -m monprojet.train` (dans `TP/TP0`) :

| Modèle | Rappel (principale) | Précision | Accuracy | F1 |
|---|---|---|---|---|
| Baseline (classe majoritaire) | 0,000 | 0,000 | 0,824 | 0,000 |
| **Régression logistique** (`class_weight="balanced"`) | **0,847** | 0,527 | 0,839 | 0,649 |
| Arbre de décision (`class_weight="balanced"`) | 0,540 | 0,572 | 0,848 | 0,556 |
| Forêt aléatoire | 0,534 | 0,712 | 0,880 | 0,610 |

Pour comparaison, la régression logistique **sans** `class_weight` obtient un rappel de 0,574 (précision 0,737) sur le même jeu de test.

## Décision
**Modèle retenu : la régression logistique avec `class_weight="balanced"`.**

- Meilleur rappel : 84,7 % des pannes détectées, contre 0 % pour la baseline (+0,847) et ≈ 54 % pour l'arbre et la forêt (+0,31).
- **Critère d'acceptation — rappel ≥ 0,75 et précision ≥ 0,50 sur le jeu de test (20 %) : atteint** (0,847 et 0,527).
- La forêt aléatoire a la meilleure accuracy (0,880) mais rate près d'une panne sur deux : l'accuracy n'est pas la bonne métrique ici (la baseline fait 0,824 sans détecter une seule panne).
- Modèle simple, rapide, explicable à l'équipe de maintenance (un coefficient par capteur).
- Prix du choix : précision 0,527, soit environ une fausse alerte par vraie panne détectée — une heure d'inspection, acceptable face à une journée d'arrêt.

## Limites
- **Données synthétiques** : ces scores ne disent rien de vraies machines.
- **Un seul jeu de test** de ≈ 176 pannes : incertitude d'environ ±0,05 sur le rappel ; une validation croisée donnerait une fourchette.
- **Pas de réglage** des hyperparamètres ni du seuil (0,5 ici ; l'API du TP1 utilise 0,3) ; choisir le seuil demanderait un jeu de validation séparé, pour ne pas « tricher » sur le test.
- **Pas de dimension temporelle** : les relevés sont traités comme indépendants ; une machine qui se dégrade demanderait un historique et un découpage chronologique.
