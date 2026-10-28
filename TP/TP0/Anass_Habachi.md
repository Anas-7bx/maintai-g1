# TP0 : MaintAI
**Nom :** Anass Habachi · **Groupe :** G1

## Le problème
Prédire une panne à partir de 4 capteurs (température, vibration, charge, heures de fonctionnement) ; une panne manquée arrête une ligne.

## Résultats sur le jeu de test
| Modèle | Accuracy | Rappel | Précision |
|---|---|---|---|
| baseline | 0.824 | 0.000 | 0.000 |
| régression logistique | 0.839 | 0.847 | 0.527 |
| arbre de décision | 0.848 | 0.540 | 0.572 |
| forêt aléatoire | 0.880 | 0.534 | 0.712 |

## Mon choix, et pourquoi
Je choisis la **régression logistique**.

- Dans MaintAI, une panne manquée arrête une ligne de production : c'est l'erreur la plus grave. La métrique qui compte le plus est donc le **rappel** (la part des vraies pannes qu'on détecte).
- La régression logistique a le meilleur rappel (0,847) : elle détecte environ 85 % des pannes.
- La forêt aléatoire a la meilleure accuracy (0,880), mais elle rate presque une panne sur deux (rappel 0,534). Une bonne accuracy ne suffit pas ici.
- C'est aussi un modèle simple, rapide et plus facile à expliquer qu'une forêt.

## Le critère (rappel >= 0,75) est-il atteint ?
Oui, avec la régression logistique : rappel de 0,847, au-dessus de 0,75. Les autres modèles ne l'atteignent pas (0,540 pour l'arbre, 0,534 pour la forêt).

Ce résultat vient du réglage `class_weight="balanced"` : les pannes sont rares (environ 18 % des relevés), donc le modèle leur donne plus de poids pendant l'entraînement pour ne pas les ignorer.

Le prix à payer est la **précision** (0,527) : environ une alerte sur deux est une fausse alerte. Pour une usine, c'est acceptable, car une inspection pour rien coûte beaucoup moins cher qu'une ligne arrêtée.

## Ce qui reste flou
- La baseline a une accuracy de 0,824 alors qu'elle ne détecte aucune panne : elle prédit toujours « pas de panne » et 82 % des relevés sont sans panne. Ça montre que l'accuracy peut être trompeuse, et je dois encore apprendre à m'en méfier.
- Comment choisir le bon compromis entre rappel et précision : est-ce qu'on pourrait changer le seuil de décision (0,5 par défaut) au lieu d'utiliser `class_weight` ?
- Est-ce que les résultats resteraient les mêmes avec un autre découpage des données (une autre graine `SEED`), ou est-ce qu'ils dépendent du hasard ?
