# Admin quickstart — Gemini provider pool

After applying migrations, an authenticated user with role `ADMIN` can manage provider configurations.

## Add a Gemini API configuration

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/api/v1/admin/ai-providers `
  -Headers @{ Authorization = "Bearer ADMIN_ACCESS_TOKEN" } `
  -ContentType 'application/json' `
  -Body '{"name":"gemini-project-a","provider":"gemini","api_key":"YOUR_GEMINI_KEY","model":"gemini-3.5-flash","priority":10,"enabled":true}'
```

## Add a Vertex AI configuration

```json
{
  "name": "vertex-project-a",
  "provider": "vertex_ai",
  "project_id": "my-google-cloud-project",
  "location": "us-central1",
  "model": "gemini-2.5-flash",
  "priority": 20,
  "enabled": true
}
```

Use `GET /api/v1/admin/ai-providers` to inspect health metadata. The API never returns API keys. Use `POST /{id}/reset` after fixing a provider that entered cooldown. The admin API must never be exposed to candidate users.
