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

   > 💡 Pour une démonstration locale rapide (sans Docker), exécutez simplement `python start.py` (ou double-cliquez sur `start.command` sur macOS) : la base est créée, la démo est
   > chargée et l'API + le tableau de bord se lancent automatiquement.

3. **Configurer les variables d'environnement**
   Créez un fichier `.env` contenant :
   ```env
   EMP_DATABASE__URL=postgresql+psycopg2://empathy:password@db/empathy
   EMP_OPENAI__API_KEY=sk-...
   EMP_TWILIO__ACCOUNT_SID=AC...
   EMP_TWILIO__AUTH_TOKEN=...
   EMP_FLEXPRICE__API_KEY=...
   EMP_NOTIFICATIONS__ENABLED=true
   ```

4. **Docker Compose prêt à l'emploi**
   Un fichier `docker-compose.yaml` est fourni. Il installe PostgreSQL, l'API et le front.

   ```bash
   docker compose up --build -d
   ```

   L'API écoute sur `http://localhost:8000` et le tableau de bord sur `http://localhost:5173`.

5. **Initialiser / recharger la démo**
   Le service `api` exécute `python scripts/init_db.py --seed-demo` au démarrage. Pour forcer une régénération :

   ```bash
   docker compose exec api python -m project_empathy.cli seed-demo --force
   ```

   Récupérez ensuite la clé API de démonstration (affichée dans les logs et stockée dans `data/demo_api_key.txt`). Vous pouvez également générer des clés supplémentaires :

   ```bash
   docker compose exec api python -m project_empathy.cli create-token 1 --name "Dashboard"
   ```

6. **Configurer Twilio**
   - Créer un numéro Voice et pointer les webhooks vers `https://votredomaine/api/v1/twilio/voice`.
   - Activer la transcription temps réel si disponible.
   - Ouvrir les flux sortants HTTPS si les webhooks doivent joindre Zapier/Slack/CRM.

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
