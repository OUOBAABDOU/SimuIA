# IARH — Flutter + FastAPI

Plateforme de simulation d'entretiens assistés par IA. **`frontend/` est l'unique client Flutter officiel ; `backend/` est l'unique backend FastAPI officiel.**

## Architecture locale officielle

```text
Flutter Web/Nginx
        │
        ▼
     FastAPI
        │
 ┌──────┼─────────┐
 ▼      ▼         ▼
Postgres Redis    MinIO
        │          ▲
        ▼          │
      Celery       │
        │          │
   Whisper/Gemini  │
        ▲          │
        │          │
 LiveKit → Egress ──┘
```

## 1. Méthode recommandée : tout le projet dans Docker

Prérequis : Docker Desktop.

```powershell
docker compose config
docker compose up --build -d
docker compose ps
```

URLs locales :

- Frontend : `http://localhost`
- FastAPI : `http://localhost:8000/docs`
- Readiness : `http://localhost:8000/api/v1/health/ready`
- MinIO : `http://localhost:9001`

Logs :

```powershell
docker compose logs -f
docker compose logs -f backend
docker compose logs -f celery_worker
docker compose logs -f livekit_egress
```

Arrêt :

```powershell
docker compose down
```

Réinitialisation complète des volumes (destructif) :

```powershell
docker compose down -v
docker compose up --build -d
```

## 2. Démarrer tout avec le script local

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-all.ps1
```

Le script doit valider `docker compose config`, démarrer les services, attendre le readiness FastAPI et afficher l'état.

Arrêt :

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop-all.ps1
```

## 3. Backend Docker + Flutter local

```powershell
docker compose up --build -d
cd frontend
flutter pub get
flutter analyze
flutter test
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

Cette méthode est recommandée pour le développement Flutter grâce au hot reload.

## 4. PostgreSQL local + FastAPI local

Installer PostgreSQL, créer `iarh`, puis configurer `DATABASE_URL` dans l'environnement backend.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Redis/MinIO/LiveKit/Egress peuvent rester dans Docker :

```powershell
docker compose up -d redis minio minio_init livekit livekit_egress
```

## 5. Sans Docker

Installer localement PostgreSQL, Redis, MinIO, LiveKit et Egress, puis lancer : PostgreSQL → Redis → MinIO → LiveKit → Egress → FastAPI → Celery → Flutter. Cette méthode est réservée au diagnostic et n'est pas la méthode locale recommandée.

## 6. Flutter Android

Émulateur :

```powershell
flutter run -d <DEVICE_ID> --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Téléphone physique : utiliser l'IP LAN du PC, par exemple `http://192.168.1.20:8000`, avec le PC et le téléphone sur le même réseau.

## 7. LiveKit local

Dans Docker, FastAPI utilise `ws://livekit:7880` et le navigateur utilise `ws://localhost:7880`. Pour un téléphone physique, utiliser l'IP LAN du PC. En production, utiliser HTTPS/WSS.

## 8. Workflow métier garanti

Le pipeline d'entretien est :

```text
ACTIVE
  ↓ FINISH
PROCESSING
  ↓ Egress terminé
TRANSCRIBING
  ↓ toutes les transcriptions prêtes
EVALUATING
  ↓ Gemini
COMPLETED
```

Un rapport **ne peut pas être généré** si une réponse audio/vidéo possède un enregistrement sans transcription.

Les échecs de média passent par `FAILED` et ne doivent pas laisser silencieusement un entretien bloqué.

## 9. Migrations

La migration `0012_interview_processing_states` ajoute les états `PROCESSING`, `TRANSCRIBING`, `EVALUATING` et `FAILED`.

Docker :

```powershell
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
```

Local :

```powershell
cd backend
alembic current
alembic upgrade head
```

## 10. Tests

Frontend :

```powershell
cd frontend
flutter analyze
flutter test
```

Backend :

```powershell
cd backend
pytest
```

Tests E2E manuels :

```text
Inscription → Connexion → Simulation → Entretien → START
→ Questions/Réponses → FINISH → Egress → MinIO
→ Transcription → Évaluation → Rapport
```

## 11. Checklist de validation

- [ ] `docker compose config` OK
- [ ] PostgreSQL healthy
- [ ] Redis healthy
- [ ] MinIO healthy + bucket `iarh-media`
- [ ] LiveKit démarré
- [ ] Egress démarré
- [ ] FastAPI `/health/ready` OK
- [ ] Celery connecté à Redis
- [ ] Flutter Web accessible
- [ ] `flutter analyze` OK
- [ ] `flutter test` OK
- [ ] `pytest` OK
- [ ] Auth OK
- [ ] Simulation OK
- [ ] Entretien OK
- [ ] LiveKit/caméra/micro OK
- [ ] Egress → MinIO OK
- [ ] Transcription OK
- [ ] Évaluation uniquement après transcription
- [ ] Rapport OK

## 12. Dépannage

```powershell
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 celery_worker
docker compose logs --tail=100 livekit
docker compose logs --tail=100 livekit_egress
```

Si le backend est `unhealthy`, tester :

```powershell
curl http://localhost:8000/api/v1/health/ready
```

Si la transcription est lente au premier lancement, le modèle Faster-Whisper peut devoir être téléchargé.

## 13. Variables d'environnement

Utiliser `.env.example` comme référence. Les secrets présents dans le Compose sont uniquement des valeurs de développement local. Ne jamais réutiliser ces secrets en production.

## 14. Build with Gemini XPRIZE

The competition package is documented in `COMPETITION_SUBMISSION.md`,
`docs/DEVPOST_SUBMISSION_EN.md`, `docs/TEST_INSTRUCTIONS_EN.md` and
`docs/SUBMISSION_EVIDENCE_TEMPLATE_EN.md`. The deployment path is in
`docs/CLOUD_RUN_DEPLOYMENT.md`.

The application uses Gemini through the Google GenAI SDK. For the judge
environment, set `VERTEX_AI_ENABLED=true`, `GOOGLE_CLOUD_PROJECT` and a
production service identity with Vertex AI User permission, then deploy the
backend on Cloud Run. A successful Gemini evaluation must be demonstrated in
Cloud Logging; configuration alone is not evidence of an API call.

The interview consent screen explicitly tells users that recordings,
transcripts and anonymized usage evidence may be shared with authorized
evaluators. Share only data for which the user has given permission.

## 15. Architecture unique

```text
backend/   → FastAPI, PostgreSQL, Celery, Gemini/Vertex AI
frontend/  → Flutter Web, Android et iOS
```

Tous les clients utilisent le même `frontend/` et le même contrat API. Toute nouvelle fonctionnalité doit être ajoutée dans ces deux sources officielles.

## 15. Test local rapide

Depuis la racine du projet :

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose ps
Invoke-WebRequest http://localhost:8000/api/v1/health
Invoke-WebRequest http://localhost:8000/api/v1/health/ready
```

Dans un second terminal :

```powershell
cd frontend
flutter pub get
flutter analyze
flutter test
flutter run -d chrome --dart-define=API_BASE_URL=http://localhost:8000
```

Pour tester le backend :

```powershell
cd backend
pip install .
pip install pytest pytest-asyncio httpx ruff
pytest -q
```

Pour arrêter les services :

```powershell
docker compose down
```

Le pool Gemini admin est documenté dans `docs/AI_PROVIDER_ADMIN_QUICKSTART.md`.
