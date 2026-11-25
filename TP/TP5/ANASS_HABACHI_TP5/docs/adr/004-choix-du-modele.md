# ADR 004 : choix du modèle et du seuil d'alerte de MaintAI

Date : 25/11/2026 · Auteurs : Anass Habachi

## Contexte
MaintAI doit prévenir les pannes à partir des relevés de capteurs. Une panne manquée coûte beaucoup plus cher qu'une
fausse alerte : le critère principal est donc le recall (part des vraies pannes détectées), la precision passant au
second plan. Les pannes sont rares (environ 13,6 % des relevés), si bien que l'accuracy est trompeuse : le baseline qui
ne prédit jamais de panne atteint déjà 0.864.

Tous les runs comparés ci-dessous ont été suivis dans MLflow (expérience `maintai`) et entraînés sur la même version
des données (DVC, v1, `data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15`, 4000 relevés d'entraînement, 1000 de test).

## Options étudiées

| Option | run_id (8 car.) | recall | precision | accuracy |
|---|---|---|---|---|
| Régression logistique, C = 1.0, seuil 0.3 (défaut) | `3f657566` | 0.750 | 0.622 | 0.904 |
| Régression logistique, C = 0.01, seuil 0.3 | `9be23a8b` | 0.691 | 0.653 | 0.908 |
| **Régression logistique, C = 1.0, seuil 0.2** | **`1a0577d6`** | **0.838** | **0.543** | **0.882** |
| Régression logistique, C = 1.0, seuil 0.15 | `bcfb123f` | 0.875 | 0.500 | 0.864 |
| Forêt aléatoire (200 arbres), seuil 0.3 | `c5b1dc51` | 0.728 | 0.562 | 0.886 |

1. **Régression logistique, seuil 0.3** : bon équilibre, mais elle rate une panne sur quatre.
2. **C = 0.01** : moins de fausses alertes, mais elle rate encore plus de pannes (recall 0.691). C'est écarté.
3. **Seuil 0.2** : elle rate environ une panne sur six, avec un peu plus d'une fausse alerte pour une vraie.
4. **Seuil 0.15** : le meilleur recall, mais une alerte sur deux est fausse, et l'accuracy n'est pas meilleure que celle
   du baseline.
5. **Forêt aléatoire** : plus complexe, plus lente et moins lisible, et moins bonne que la régression logistique en
   recall comme en precision. C'est écarté.

## Décision
Nous retenons la **régression logistique (C = 1.0) avec un seuil d'alerte de 0.2**.

- Run MLflow : `1a0577d646b24334b480ca57e3297766`
- Données : `data_md5` = `73e0b7cb3c6f795c70c3ddf970b99c15` (commit `52cbd65 Données v1`)

Raison principale : c'est le meilleur compromis pour la contrainte du projet. Le recall passe de 0.750 à 0.838 par
rapport au réglage par défaut, en gardant une precision supérieure à 0.5. Le seuil 0.15 détecte un peu plus de pannes
(+3,7 points de recall), mais au prix d'une fausse alerte pour chaque vraie panne.

## Conséquences
- **Ce que nous acceptons en échange :** plus de fausses alertes. La precision passe de 0.622 à 0.543, donc environ
  46 % des alertes ne correspondront pas à une panne. Ces alertes coûtent une inspection inutile, ce qui reste moins cher
  qu'une panne non détectée.
- **Ce que la décision facilite :** le modèle est simple, rapide et explicable (coefficients de la régression). Il est
  traçable : le run MLflow donne les paramètres, les métriques, le modèle et les versions exactes des bibliothèques
  (`scikit-learn==1.8.0`), et le `data_md5` permet de retrouver les données avec DVC.
- **Ce qu'il faudra surveiller :** le nombre de fausses alertes réellement supportable par l'équipe de maintenance, et
  la dérive des données. Un run sur la v2 des données (`4496701a`, seuil 0.3) donne un recall de 0.741 : avant de changer
  de version des données, il faudra ré-entraîner au seuil 0.2 et comparer les modèles sur un même jeu de test.
