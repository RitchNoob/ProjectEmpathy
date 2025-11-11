# Project Empathy – IA réceptionniste pour restaurants

Project Empathy est une plate-forme SaaS destinée aux restaurateurs. Elle connecte leur numéro Twilio à une IA conversationnelle capable de répondre aux clients 24 h/24, de prendre des commandes, de gérer les réservations et de suivre la facturation via des abonnements Flexprice ou Stripe Billing.

## Fonctionnalités principales

- **Téléphonie Twilio Voice** : webhook FastAPI pour accueillir l'appelant et boucler sur les transcriptions. L'IA répond en français et conserve l'historique de l'appel.
- **IA conversationnelle** : intégration OpenAI (ou compatbile) avec prompt "réceptionniste de restaurant". L'IA propose des ventes additionnelles, confirme les commandes et pose des questions de clarification.
- **Gestion du menu** : CRUD complet pour catégories et plats, utilisé par l'IA et exposé dans le tableau de bord.
- **Prise de commandes et réservations** : stockage structuré, calcul des montants, suivi du statut et enregistrement du contexte d'appel.
- **Abonnements Flexprice/Stripe** : synchronisation de plans, suivi des crédits, blocage des fonctionnalités en cas de dépassement.
- **Dashboard restaurateur** : statistiques (nombre d'appels, commandes, panier moyen, CA) exposées via API pour un tableau de bord statique prêt à l'emploi.
- **Designer du réceptionniste** : profil IA par restaurant avec tonalité, langues, phrases d'upsell et palette personnalisables depuis le tableau de bord ou l'API.
- **Clés API rotatives** : génération, rotation et révocation de jetons par restaurant pour sécuriser l'accès au tableau de bord et aux intégrations externes.
- **Notifications webhook** : endpoints configurables par restaurant, signatures HMAC et suivi des livraisons pour intégrer Project Empathy avec Zapier, Slack, POS ou CRM.

## Structure du dépôt

```
project/
├── src/project_empathy
│   ├── main.py                # Application FastAPI et configuration CORS
│   ├── config.py              # Paramètres (DB, Twilio, OpenAI, Flexprice)
│   ├── db.py                  # Session SQLAlchemy
│   ├── models/                # ORM (restaurants, menu, commandes, abonnements…)
│   ├── schemas/               # Schémas Pydantic (API)
│   ├── services/              # Logique métier (commandes, stats, téléphonie)
│   ├── api/                   # Routes FastAPI v1
│   ├── ai/assistant.py        # Orchestrateur OpenAI
│   └── billing/flexprice.py   # Client Flexprice minimal
├── dashboard/                 # Tableau de bord statique clé en main
├── frontend/                  # (Optionnel) source React originale
├── tests/                     # Tests Pytest des endpoints principaux
├── config.example.yaml        # Exemple de configuration
├── requirements.txt           # Dépendances backend
└── README.md
```

## Prérequis

- Python 3.10+
- PostgreSQL (prod) ou SQLite (développement)
- Comptes Twilio, OpenAI/Mistral et Flexprice/Stripe

## Démarrage rapide (clé en main)

Une fois Python 3.10+ et les dépendances installées (`pip install -r requirements.txt`), il suffit d'une seule commande pour tout lancer :

```bash
python start.py
```

Le script `start.py` appelle la commande `empathy launch` qui :

- crée la base de données et les tables si nécessaire ;
- recharge les données de démonstration et la clé API (stockée dans `data/demo_api_key.txt`) ;
- génère le tableau de bord statique et sa configuration (`dashboard/runtime-config.json`) ;
- démarre l'API FastAPI via le serveur HTTP intégré ainsi qu'un serveur web local pour le tableau de bord ;
- ouvre automatiquement votre navigateur sur `http://localhost:5173`.

Arrêtez l'application avec `Ctrl+C` dans le terminal. Pour repartir d'une base vierge, relancez `python start.py --reseed` ou utilisez la commande CLI `python -m project_empathy.cli launch --reseed`.

### Notifications temps réel

Chaque restaurant peut enregistrer des webhooks via le tableau de bord (onglet **Notifications en temps réel**) ou l'API REST (`/api/v1/restaurants/{id}/notifications/`). À chaque commande, réservation ou appel, Project Empathy envoie une requête POST signée avec HMAC SHA-256 (en-tête `X-ProjectEmpathy-Signature`) pour sécuriser l'intégration. Les tentatives sont historisées avec le statut HTTP et le dernier message d'erreur éventuel.

Configurer un webhook depuis la CLI/HTTP :

```bash
curl -X POST \
  -H "X-API-Key: <clé_api>" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/restaurants/1/notifications/ \
  -d '{
    "name": "Zapier",
    "target_url": "https://hooks.zapier.com/...",
    "events": ["orders.created", "reservations.created"],
    "secret": "change-me"
  }'
```

Pour désactiver globalement les webhooks (par exemple en développement hors ligne), définissez `EMP_NOTIFICATIONS__ENABLED=false` ou modifiez la section `notifications` dans `config.yaml`.

## Installation backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml  # puis éditer
python -m project_empathy.cli runserver
```

Le serveur autonome s'appuie exclusivement sur la bibliothèque standard : aucune dépendance externe comme Uvicorn n'est requise, ce qui simplifie les déploiements hors ligne.

### Variables d'environnement

Les paramètres sont chargés via des variables `EMP_` (voir `config.py`). Exemple :

```bash
export EMP_DATABASE__URL="postgresql+psycopg2://user:pass@localhost/empathy"
export EMP_OPENAI__API_KEY="sk-..."
export EMP_TWILIO__ACCOUNT_SID="AC..."
export EMP_TWILIO__AUTH_TOKEN="..."
```

## Base de données

Le script `scripts/init_db.py` et la commande `python -m project_empathy.cli init-db` créent les tables SQLAlchemy. Ajoutez `--seed-demo` pour générer un restaurant complet en quelques secondes.

```bash
python scripts/init_db.py
```

En production, configurez PostgreSQL puis exécutez le script. SQLite reste pratique pour les tests locaux.

## Tableau de bord web

L'interface prête à l'emploi se situe dans le dossier `dashboard/`. Elle est servie telle quelle par le script `start.py` ou n'importe quel serveur HTTP statique.

- `index.html` : structure et sections (statistiques, menu, commandes, réservations, designer du concierge)
- `styles.css` : thème sombre premium en glassmorphisme, piloté par les couleurs de votre concierge
- `app.js` : consommation des endpoints `/api/v1/...` avec la clé API de démonstration et synchronisation du profil IA

La configuration générée (`dashboard/runtime-config.json`) indique l'URL de l'API et la clé à utiliser. Relancez `python start.py --reseed` pour régénérer la démo et le fichier de configuration.

> Besoin de personnaliser le front ? Les sources React d'origine restent disponibles dans `frontend/` (nécessite Node.js 18+ et npm).

### Personnaliser le concierge IA

Chaque restaurant dispose désormais d'un profil « réceptionniste » stocké côté serveur. Il définit l'identité vocale et visuelle de l'agent : nom d'usage, message d'accueil, ton, langues maîtrisées, phrases d'upsell, instructions spécifiques et palette de couleurs. Deux façons de le modifier :

1. **Depuis le tableau de bord statique** : le panneau « Designer du réceptionniste » combine aperçu en temps réel, badge de synchronisation et nouveau playbook conversationnel. Chaque modification de ton, de langues ou d'instructions régénère instantanément la palette, la carte mobile et le script IA prévisualisé.
2. **Via l'API REST** :

   ```bash
   curl -X PATCH \
     -H "X-API-Key: <clé_api>" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/v1/restaurants/1/receptionist/profile \
     -d '{
       "display_name": "Concierge Lumière",
       "tone": "Chaleureux et haute couture",
       "upsell_phrases": [
         "Mettre en avant notre dégustation saisonnière",
         "Proposer l'accord mets & vins premium"
       ],
       "brand_primary_color": "#7060FF",
       "brand_accent_color": "#38E8FF"
     }'
   ```

   La réponse retourne l'objet `ReceptionistProfile` complet. Toute mise à jour s'applique automatiquement aux invites envoyées à l'IA (salutations, upsell, signature) ainsi qu'à l'expérience Twilio (greeting, langue et voix). Vous pouvez également interroger `GET /api/v1/restaurants/{id}/receptionist/preview` pour récupérer le script consolidé exposé dans le playbook du tableau de bord.

## Documentation API

La documentation interactive est disponible sur `http://localhost:8000/docs` grâce à FastAPI. Un aperçu textuel est fourni dans `docs/api.md` (endpoints de création de restaurants, menus, commandes, réservations, etc.).

## Tests

```bash
pytest
```

## CLI d'administration

Une interface en ligne de commande simplifie les opérations courantes :

```bash
python -m project_empathy.cli init-db --seed-demo      # Créer les tables et charger la démo (avec clé API)
python -m project_empathy.cli seed-demo --force        # Régénérer les données d'exemple
python -m project_empathy.cli config --json            # Afficher la configuration active
python -m project_empathy.cli stats                    # Statistiques agrégées du premier restaurant
python -m project_empathy.cli create-token 1 --name "Dashboard"  # Générer une clé API supplémentaire
```

## Orchestration Docker Compose

Pour obtenir un environnement complet (PostgreSQL + API + front React) en une commande :

```bash
docker compose up --build
```

Le service `api` initialise automatiquement la base et charge la démo si nécessaire. Le front est ensuite accessible sur `http://localhost:5173` et l'API sur `http://localhost:8000`.

## Déploiement

- Construire l'image Docker (exemple dans `docs/deployment.md` ou via `docker compose build`).
- Configurer les variables d'environnement (voir ci-dessus).
- Utiliser `ngrok http 8000` pour exposer le webhook Twilio en développement.
- Activer HTTPS (Traefik, Caddy, nginx) en production.

## Sécurité & conformité

- Secrets en variables d'environnement, jamais en clair dans le dépôt.
- HTTPS obligatoire et rotation régulière des clés API.
- Données personnelles anonymisées sur demande, conformément au RGPD.
- Pas de stockage des cartes bancaires : déléguer à Stripe/Flexprice.

## Licence

Projet sous licence MIT.
