# TP0 : MaintAI
**Nom :** Moad Bakouch · **Groupe :** G1

## Le problème
Prédire si une machine va tomber en panne à partir de 4 capteurs : température, vibration, charge et heures de fonctionnement. Chaque matin, l'équipe de maintenance choisit les machines à inspecter. Une panne manquée arrête une ligne de production une journée, alors qu'une fausse alerte ne coûte qu'une heure d'inspection. C'est donc le **rappel** qui compte en premier.

Données : `data/exemple_pannes.csv`, 5 000 relevés synthétiques, 17,6 % de pannes. Découpage aléatoire stratifié, 20 % en test, graine 42.

## Résultats sur le jeu de test
| Modèle | Accuracy | Rappel | Précision |
|---|---|---|---|
| baseline (toujours « pas de panne ») | 0.824 | 0.000 | 0.000 |
| régression logistique | 0.889 | 0.574 | 0.737 |
| forêt aléatoire | 0.881 | 0.557 | 0.705 |
| gradient boosting | 0.881 | 0.574 | 0.697 |
| régression logistique équilibrée (`class_weight="balanced"`) | 0.839 | **0.847** | 0.527 |

## Mon choix, et pourquoi
- Je retiens la **régression logistique équilibrée**, parce qu'elle a le meilleur rappel : elle détecte 85 % des pannes, contre 57 % pour les autres modèles et 0 % pour la baseline.
- Son accuracy est la plus basse des vrais modèles, mais ce n'est pas la bonne métrique : la baseline a 82 % d'accuracy sans détecter une seule panne.
- La forêt aléatoire et le gradient boosting ne font pas mieux que la régression logistique. Je garde donc le modèle le plus simple et le plus explicable.
- Le prix à payer : environ une alerte sur deux est fausse (précision 0,527). Une heure d'inspection perdue reste acceptable face à une journée d'arrêt.

## Le critère (rappel >= 0,75) est-il atteint ?
- Avec la régression logistique « simple » : **non** (rappel 0,574). C'est un résultat valable : le modèle apprend, mais avec le seuil de 0,5 il est trop prudent sur la classe minoritaire.
- Avec `class_weight="balanced"` : **oui**, rappel 0,847 ≥ 0,75 et précision 0,527 ≥ 0,50 sur le jeu de test de 20 %. Pondérer les pannes revient à baisser le seuil de décision. On aurait aussi pu garder le modèle simple et choisir un seuil de 0,3, comme le fait l'API du TP1.

## Ce qui reste flou
- Comment choisir le seuil de décision proprement, sans « tricher » sur le jeu de test ?
- Les scores obtenus sur des données synthétiques seront-ils proches sur de vraies machines ?
