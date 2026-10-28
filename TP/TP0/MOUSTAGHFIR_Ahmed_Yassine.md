# TP0 : MaintAI
**Nom :** MOUSTAGHFIR Ahmed Yassine · **Groupe :** G1

## Le problème
Prédire une panne à partir de 4 capteurs (température, vibration, charge, heures de fonctionnement) ; une panne manquée arrête une ligne.

## Résultats sur le jeu de test
| Modèle | Accuracy | Rappel | Précision |
|---|---|---|---|
| baseline | 0.824 | 0.000 | 0.000 |
| régression logistique | 0.889 | 0.574 | 0.737 |
| régression logistique équilibrée | — | 0.847 | 0.527 |

## Mon choix, et pourquoi
Je retiens la **régression logistique équilibrée**.

- Dans MaintAI, une panne manquée arrête une ligne : c'est l'erreur la plus grave. Le critère demandé porte donc sur le **rappel** (au moins 0,75) et, en même temps, sur la **précision** (au moins 0,50), pour ne pas noyer l'atelier sous les fausses alertes.
- La régression logistique simple a la meilleure accuracy du tableau (0,889) et une précision de 0,737, mais son rappel n'est que de 0,574 : elle rate trop de pannes.
- La baseline a une accuracy de 0,824 et un rappel de 0. Elle prédit toujours « pas de panne ». Elle ne détecte rien.
- La version équilibrée (`class_weight="balanced"`) est la seule qui passe les deux seuils : rappel 0,847 et précision 0,527. Les pannes sont rares (environ 18 % des relevés) ; ce réglage leur donne plus de poids à l'entraînement.

## Le critère (rappel ≥ 0,75 et précision ≥ 0,50) est-il atteint ?
Oui, avec la régression logistique équilibrée : rappel de 0,847 (≥ 0,75) et précision de 0,527 (≥ 0,50).

La régression logistique sans équilibrage n'atteint pas le rappel (0,574). La baseline n'atteint ni le rappel ni la précision.

Le prix du rappel est une précision de 0,527 : environ une alerte sur deux est une fausse alerte. Une inspection pour rien coûte moins cher qu'une ligne arrêtée, donc ce compromis est acceptable.

## Ce qui reste flou
- La baseline affiche 0,824 d'accuracy sans détecter aucune panne. L'accuracy suit la classe majoritaire (« pas de panne ») et peut donc tromper.
- La régression logistique simple a une meilleure accuracy (0,889) et une meilleure précision (0,737), mais elle est écartée à cause du rappel. Je dois encore voir si un autre seuil que 0,5 permettrait de garder ce modèle tout en passant 0,75 de rappel, sans `class_weight`.
- Le critère ne regarde pas l'accuracy. La régression logistique simple a pourtant 0,889, au-dessus de la version retenue. Faut-il quand même la montrer au responsable, ou seul le couple rappel / précision compte ?
- Ces scores dépendent du découpage (20 % de test, graine 42). Une autre graine changerait-elle le modèle retenu ?
