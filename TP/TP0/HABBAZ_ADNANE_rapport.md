# TP0 : MaintAI
**Nom :** Adnane Habbaz · **Groupe :** G1
## Le problème
Prédire une panne à partir de 4 capteurs ; une panne manquée arrête une ligne.
## Résultats sur le jeu de test
| Modèle | Accuracy | Rappel | Précision |
Train : 272 lignes | Test : 68 lignes

ridge          22.623  28.545  0.880
random_forest  31.825  41.647  0.745
decision_tree  46.000  59.710  0.475
baseline       70.271  88.416 -0.151

Meilleur modèle : ridge
mae : 22.623
| baseline | 0.824 | 0.000 | 0.000 |
| régression logistique | 0.889 | 0.574 | 0.737 |
## Mon choix, et pourquoi
mon chois serait le Ridge, il bat le baseline avec un gain de 68% 
## Le critère (rappel >= 0,75) est-il atteint ?
le r² a a tteint 0.88 > 0.75
## Ce qui reste flou
c'est bin, tout est clair 