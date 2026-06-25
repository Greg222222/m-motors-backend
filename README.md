# M-Motors — Backend API

API FastAPI pour la plateforme M-Motors (Achat / Location Longue Durée). Couvre les
User Stories US-01 à US-06 (recherche, inscription, suivi de dossier, ajout/bascule
de véhicules, validation des dossiers).

## Stack

- FastAPI + SQLAlchemy + Pydantic v2
- SQLite en local / tests, PostgreSQL managé en production (`DATABASE_URL`)
- Auth JWT (passlib `pbkdf2_sha256` pour le hash de mot de passe — pas de dépendance
  compilée, portable sur n'importe quelle version de Python)
- Logs JSON structurés + alerting webhook (Slack/Discord) sur erreur critique
- Tests `pytest` (couverture > 80%, voir ci-dessous)

## Lancer en local

```bash
python -m venv .venv
. .venv/Scripts/activate   # ou source .venv/bin/activate sous Linux/Mac
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

L'API est servie sur `http://localhost:8000` (`/health` pour vérifier qu'elle tourne,
`/docs` pour la documentation Swagger générée automatiquement).

## Tests et couverture

```bash
pytest --cov=app --cov-report=term-missing
```

Couverture mesurée : **97%** (objectif énoncé : 80%).

## Variables d'environnement

Voir `.env.example`. En production (Render), `DATABASE_URL` pointe vers
l'instance PostgreSQL managée, `ALERT_WEBHOOK_URL` vers un webhook Slack/Discord
pour recevoir les alertes en cas d'erreur critique (laissé vide = pas d'alerting,
l'app fonctionne identiquement).

## Sécurité mise en place

- Hash des mots de passe (pbkdf2_sha256, jamais de mot de passe en clair en base)
- Tokens JWT signés et expirants (`SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`)
- CORS restreint à la liste d'origines autorisées (`CORS_ORIGINS`)
- Validation stricte des entrées (Pydantic) et des fichiers uploadés (type MIME et
  taille maximale, voir `app/routers/documents.py`)
- Rate limiting sur `/auth/login` (`slowapi`, anti brute-force)
- Secrets exclusivement via variables d'environnement (`.env` non commité)

## Monitoring & alerting

- Chaque requête est journalisée en JSON structuré (`app/logging_config.py`) :
  méthode, route, code de statut, latence.
- Toute exception non gérée est journalisée avec sa trace complète et déclenche
  une alerte (`app/alerting.py`) vers un webhook Slack/Discord si configuré.
- Endpoint `/health` pour la supervision (uptime monitoring externe type
  UptimeRobot/Render health check).

## Git / branches

Stratégie GitFlow : `main` (production), `develop` (intégration), une branche
`feature/US-0X-...` par User Story, fusionnée dans `develop` puis `develop` → `main`
pour chaque release.
