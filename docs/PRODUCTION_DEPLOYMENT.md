# Production deployment checklist

Do not run the development Compose file as a production deployment. Use `.env.production` from `.env.production.example`, inject secrets through the deployment secret store, and use the production Compose override only after replacing the LiveKit and Egress configuration files with generated versions containing the same secret pair.

Required checks before rollout:

- `APP_ENV=production`.
- Non-default JWT, PostgreSQL, MinIO and LiveKit secrets.
- `LIVEKIT_PUBLIC_URL` uses `wss://`.
- `MEDIA_S3_PUBLIC_ENDPOINT` is reachable by the client and is used only for presigned URLs.
- `CORS_ORIGINS` contains only the deployed frontend origin(s).
- LiveKit and Egress use the same injected API key/secret as the backend.
- PostgreSQL, Redis, MinIO and LiveKit are on private networks; only the reverse proxy is public.
- TLS, backups, object lifecycle rules, log redaction and monitoring are enabled.
- Run migrations as a separate release step and never on every backend container start.

The application refuses to start in production when required secrets or secure public URLs are missing.
