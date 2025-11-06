# Déploiement sur serveur Ubuntu + Docker

1. **Préparer le serveur**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install docker.io docker-compose -y
   sudo usermod -aG docker $USER
   ```

2. **Cloner le dépôt et configurer l'environnement**
   ```bash
   git clone https://github.com/votre-org/project-empathy.git
   cd project-empathy
   cp config.example.yaml config.yaml
   nano config.yaml  # renseigner les secrets
   ```

3. **Configurer les variables d'environnement**
   Créez un fichier `.env` contenant :
   ```env
   EMP_DATABASE__URL=postgresql+psycopg2://empathy:password@db/empathy
   EMP_OPENAI__API_KEY=sk-...
   EMP_TWILIO__ACCOUNT_SID=AC...
   EMP_TWILIO__AUTH_TOKEN=...
   EMP_FLEXPRICE__API_KEY=...
   ```

4. **Docker Compose (exemple)**
   ```yaml
   version: "3.9"
   services:
     api:
       build: .
       command: uvicorn project_empathy.main:app --host 0.0.0.0 --port 8000
       env_file: .env
       ports:
         - "8000:8000"
       depends_on:
         - db
     db:
       image: postgres:15
       restart: unless-stopped
       environment:
         POSTGRES_USER: empathy
         POSTGRES_PASSWORD: password
         POSTGRES_DB: empathy
       volumes:
         - db_data:/var/lib/postgresql/data
   volumes:
     db_data:
   ```

5. **Initialiser la base**
   ```bash
   docker-compose run --rm api python scripts/init_db.py
   ```

6. **Configurer Twilio**
   - Créer un numéro Voice et pointer les webhooks vers `https://votredomaine/api/v1/twilio/voice`.
   - Activer la transcription temps réel si disponible.

7. **Certificats & HTTPS**
   - Utiliser Traefik ou Caddy pour le TLS automatique.
   - Ajouter des règles de pare-feu (UFW) pour n'exposer que les ports nécessaires.

8. **Observabilité**
   - Activer les métriques FastAPI/Prometheus via un middleware (optionnel).
   - Centraliser les logs (Loki/ELK) pour audit RGPD.

9. **Ngrok en développement**
   ```bash
   ngrok http 8000
   ```
   Utilisez l'URL fournie pour tester le webhook Twilio depuis votre machine locale.
