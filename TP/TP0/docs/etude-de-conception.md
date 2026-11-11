# Étude de conception — MaintAI

Groupe : G1 — Anass Habachi, Adnane Habbaz, Ahmed Yassine Moustaghfir, Moad Bakouch · Version : finale · Date : 11/11/2026

## 1. Contexte et utilisateurs
- Utilisateur principal : le **responsable de l'équipe de maintenance** de l'usine, qui planifie chaque matin les inspections.
- Utilisateurs secondaires : les techniciens, qui consultent une prédiction pour une machine (interface Streamlit, commande `maintai-predict`), et les autres logiciels de l'usine (tableau de bord, système d'atelier), qui appellent l'API.

## 2. Problème et décision
- Décision prise avec le système : **quelles machines inspecter aujourd'hui**. Le système classe les machines par probabilité de panne et lève une alerte au-dessus d'un seuil.
- Fréquence : une fois par jour, le matin, pour chaque machine (avec possibilité de prédiction à la demande).
- Coût d'une erreur, et pour qui :
  - **Panne manquée (faux négatif)** : une ligne de production arrêtée une journée. C'est l'usine qui paie (production perdue, retards de livraison, réparation en urgence). C'est l'erreur la plus coûteuse.
  - **Fausse alerte (faux positif)** : une heure d'inspection inutile, payée par l'équipe de maintenance. Trop de fausses alertes, et l'équipe finit par ignorer le système.

## 3. Approche par sous-problème
| Sous-problème | Approche (règles / ML / DL / LLM / RAG) | Pourquoi pas une approche plus simple |
|---|---|---|
| Estimer la probabilité de panne d'un relevé | ML : régression logistique (classes équilibrées) dans un pipeline avec mise à l'échelle | Des règles à seuil fixe (« température > 80 °C ») ignorent les combinaisons de facteurs : une machine moyennement chaude mais qui vibre fort et qui est ancienne. Le ML apprend ces combinaisons à partir des données. Le DL serait disproportionné pour 4 variables tabulaires et 5 000 lignes. |
| Décider d'alerter | Règle : probabilité ≥ seuil (0,3, configurable) | Une règle simple suffit et reste lisible par l'équipe ; on choisit le seuil d'après le coût des erreurs. |
| Valider les entrées | Règles : bornes physiques dans le schéma Pydantic | Pas besoin de ML : une température de 500 °C est impossible, point. |

## 4. Données
| Jeu de données | Source et licence | Volume | Données personnelles ? |
|---|---|---|---|
| `data/exemple_pannes.csv` (S3) | Synthétique, généré pour le cours ; usage pédagogique libre | 5 000 lignes, 5 colonnes, 17,6 % de pannes | Non |
| `data/sensors.csv` (TP1 → TP4) | Synthétique, généré par `python -m maintai.dataset` (graine 42) | 5 000 lignes, 5 colonnes, ≈ 13,6 % de pannes | Non |

Colonnes utiles : `temperature_c` (°C), `vibration_mm_s` (mm/s), `load_pct` (%), `runtime_hours` (h) ; cible `failure` (0/1). Aucune valeur manquante.

Premier risque du projet : les **données réelles**. Il faudra obtenir de l'usine l'historique des capteurs et le journal des pannes, avec les mêmes colonnes, et vérifier que le taux de panne et les distributions sont proches de celles des données synthétiques.

## 5. Métriques, baseline et critères d'acceptation
- **Baseline et son score** : toujours prédire « pas de panne » (`DummyClassifier(strategy="most_frequent")`). Accuracy 0,824, **rappel 0**, précision 0.
- **Métrique principale : le rappel**. Une panne manquée coûte une journée de production, contre une heure pour une fausse alerte. Il faut donc d'abord ne pas rater de pannes. L'accuracy est trompeuse : la baseline atteint 82 % sans détecter une seule panne.
- **Critère d'acceptation** : **rappel ≥ 0,75 et précision ≥ 0,50 sur le jeu de test (20 % des données, tenu à l'écart, découpage aléatoire stratifié, graine 42)**.
- Résultat : rappel 0,847 et précision 0,527 avec la régression logistique équilibrée. **Critère atteint** (voir `choix-modele.md`).

Réglages de `config.py` : `DATA_PATH = data/exemple_pannes.csv`, `TARGET = "failure"`, `TASK = "classification"`, `MAIN_METRIC = "recall"`, `SPLIT = "random"`, `TIME_COLUMN = None`, `TEXT_COLUMN = None`.

## 6. Architecture

```
                  python -m maintai.dataset          python -m maintai.train
  (capteurs) ──►  data/sensors.csv  ───────────────►  models/model.joblib
                                                      models/model_info.json  (contrat : variables, seuil, version sklearn)
                                                      models/metrics.json
                                                               │ chargé une fois au démarrage
                                                               ▼
                          ┌──────────────────────────────────────────────────────┐
  .env ──────────────────►│ API FastAPI (uvicorn)   http://localhost:8000        │
  MAINTAI_API_KEY         │   GET  /health          public                       │
  MAINTAI_CORS_ORIGINS    │   POST /v1/predict      clé X-API-Key → 401          │
                          │                         schéma Pydantic → 422        │
                          │                         modèle absent → 503          │
                          │   CORS : http://localhost:5500 seulement             │
                          └───────▲───────────────▲───────────────▲──────────────┘
                                  │ fetch (navigateur, CORS)      │ httpx (serveur Python, pas de CORS)
            web/index.html servi sur :5500        │       ui/app.py (Streamlit) sur :8501
                                          curl.exe, client Java, autres logiciels

  Sans API : maintai-predict 72 6 85 15000  (package installé par pip, lit models/ ou MAINTAI_MODELS_DIR)
```

Où tourne chaque partie : tout tourne en local sur le PC de développement, dans le dossier `TP/TPn`. L'API écoute sur le port 8000, la page web sur 5500 (`python -m http.server`) et Streamlit sur 8501. Les fichiers du modèle sont dans `models/`, les données dans `data/`, et aucun des deux n'est versionné dans Git.

## 7. Choix technologiques
| Outil | Contrainte à laquelle il répond | Ce qu'on a abandonné |
|---|---|---|
| **scikit-learn** (régression logistique) | Données tabulaires, petites, modèle à expliquer à l'équipe de maintenance | Les réseaux de neurones (PyTorch) : plus lourds, moins explicables, aucun gain attendu sur 4 variables |
| **pandas + CSV** | Données qui tiennent en mémoire, faciles à inspecter | Une base de données : inutile tant qu'on reste sur un fichier de 5 000 lignes |
| **joblib + model_info.json** | Recharger le modèle et son contrat d'entrée dans l'API | Un registre de modèles (MLflow), prévu en séance 7 |
| **FastAPI + Pydantic + uvicorn** | Plusieurs clients différents ; validation des entrées et doc `/docs` générées depuis un seul schéma | Flask : il faudrait écrire à la main la validation et la documentation |
| **Clé API dans l'en-tête `X-API-Key`, lue dans `.env`** | Réserver l'API aux programmes autorisés sans gérer de comptes utilisateurs | OAuth2 / JWT : plus sûr et plus fin, mais trop complexe pour le prototype |
| **CORS limité à une liste d'origines** | Seule la page du port 5500 doit pouvoir appeler l'API depuis un navigateur | `*` : plus simple, mais n'importe quel site pourrait utiliser l'API depuis le navigateur d'un utilisateur |
| **Page HTML + `fetch`** | Un client léger, sans installation, pour montrer que l'API est indépendante du langage | Un framework (React) : inutile pour un formulaire |
| **Streamlit** | L'équipe connaît Python, pas JavaScript, et la démo doit être prête en une séance | Une interface sur mesure (design, comptes, mobile) |
| **pyproject.toml + wheel** | Livrer une commande installable par `pip`, sans API | Docker, prévu plus tard ; un simple dossier copié, sans gestion des dépendances |
| **pytest + ruff + Git (PR, tags)** | Prouver que ça marche, garder un code propre, travailler à plusieurs | Des tests manuels uniquement |

## 8. Risques, éthique, confidentialité
- **Secrets** : la clé API est dans `.env`, ignoré par Git. `.env.example` est commité avec une fausse valeur. Une clé poussée par erreur reste dans l'historique et doit être changée. La comparaison se fait avec `secrets.compare_digest`, pour ne pas laisser fuir d'information par le temps de réponse.
- **Coût d'une erreur** : une panne manquée (environ 15 % des pannes avec le modèle retenu) coûte une journée de production à l'usine. Les fausses alertes (environ une sur deux) coûtent du temps à l'équipe et peuvent l'amener à ignorer le système. Il faut surveiller ces deux taux en production.
- **Données personnelles** : aucune. Les relevés décrivent des machines, pas des personnes. Si on ajoutait l'opérateur de la machine, cela deviendrait une donnée personnelle (RGPD / loi 09-08), et le système pourrait servir à évaluer des employés : à éviter.
- **Place de la décision humaine** : le système **recommande**, l'humain **décide**. Le responsable maintenance garde la main sur le planning et peut inspecter une machine sans alerte, ou ignorer une alerte. Le système ne doit jamais arrêter une machine automatiquement.
- **Dérive** : si les machines, les capteurs ou les conditions changent, le modèle se dégrade sans prévenir. Il faut suivre le rappel réel à partir du journal des pannes.
- **Données synthétiques** : les performances annoncées ne valent rien sur des machines réelles tant que le modèle n'a pas été réentraîné et réévalué sur leurs données.

## 9. Limites et hors périmètre
**Ce que le système ne fait pas encore :**
- Il n'est entraîné que sur des données synthétiques.
- Il ne tient pas compte du temps : pas d'historique par machine, pas de tendance, pas de découpage chronologique.
- Le seuil d'alerte (0,3) n'est pas encore optimisé à partir des coûts réels.
- Pas de déploiement sur un serveur, pas d'intégration continue, pas de suivi des modèles (prévus en séances 7 et 8 : DVC, MLflow, GitHub Actions).
- Une seule clé API partagée, sans droits différenciés (pas de 403) ni journalisation des appels.

**Ce qu'il ne fera pas :**
- Diagnostiquer la cause d'une panne ou dire quelle pièce changer.
- Décider seul d'arrêter une machine ou de commander une pièce.
- Évaluer les opérateurs ou les techniciens.
