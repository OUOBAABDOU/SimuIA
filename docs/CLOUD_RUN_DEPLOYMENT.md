# Google Cloud deployment

The competition deployment should use Google Cloud Run for the FastAPI service and Vertex AI Gemini for model calls. Cloud SQL PostgreSQL, Cloud Storage, Secret Manager, Cloud Logging and Cloud Monitoring are recommended companion services.

## Setup

1. Enable Cloud Run, Cloud Build, Artifact Registry, Vertex AI, Secret Manager and Cloud SQL APIs.
2. Create the secrets referenced by `cloudbuild.yaml`: database URL, JWT secret,
   LiveKit key/secret, storage access/secret keys, AI credential encryption key,
   SMTP host/username/password and sender address. The secret names are visible
   in the `--set-secrets` argument; values must be created by the owner of the
   Google Cloud project and must never be committed.
3. Give the Cloud Run service account Vertex AI User, Cloud SQL Client and Secret Manager Secret Accessor roles.
4. Set `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `VERTEX_AI_ENABLED=true`, `APP_ENV=production`, `CORS_ORIGINS`, `LIVEKIT_PUBLIC_URL` and `MEDIA_S3_PUBLIC_ENDPOINT`.
5. Apply `alembic upgrade head` as a release step against the production
   database before sending traffic to the new revision. Do not rely on the web
   process to run migrations on every startup.
6. Configure a public HTTPS frontend and provide its URL in `CORS_ORIGINS`.

## Evidence to capture

- Cloud Run revision and URL.
- Cloud Logging entries showing a successful Gemini evaluation.
- Vertex AI usage dashboard.
- Readiness and AI health responses.
- One complete user journey from interview start to report.

## Important production dependencies

Cloud Run hosts the HTTP backend only. The production deployment also needs a
reachable PostgreSQL database, Redis/Celery worker, object storage, and a
public LiveKit/Egress setup. The local Docker Compose stack is not a substitute
for these managed or externally reachable services. Deploy and test the worker
and media pipeline separately, then capture the complete interview-to-report
journey for the evidence register.

## Verification commands

```powershell
gcloud run services describe iarh-backend --region us-central1
Invoke-WebRequest https://[CLOUD_RUN_URL]/api/v1/health/ai
Invoke-WebRequest https://[CLOUD_RUN_URL]/api/v1/health/ready
```

The AI endpoint showing `configured` proves configuration only. The required
proof is a real evaluation followed by a redacted Cloud Logging entry showing a
successful Gemini/Vertex AI call.
