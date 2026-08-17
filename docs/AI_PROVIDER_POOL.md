# Multi-provider Gemini pool

Administrators can register several authorized Gemini or Vertex AI configurations through the protected API:

- `POST /api/v1/admin/ai-providers`
- `GET /api/v1/admin/ai-providers`
- `PATCH /api/v1/admin/ai-providers/{id}`
- `POST /api/v1/admin/ai-providers/{id}/reset`
- `DELETE /api/v1/admin/ai-providers/{id}`

Gemini API keys are encrypted at rest with `AI_CREDENTIAL_ENCRYPTION_KEY` and are never returned by the API. The router selects enabled configurations by priority, skips a cooldown after transient errors, and records failures for the admin API. There is currently no visual admin dashboard. The same project should not be duplicated merely to evade quotas: Google applies Gemini rate limits per project, so use separate authorized projects, proper billing/quota configuration, or Vertex AI for production capacity.

For local development, generate a Fernet-compatible secret or use a long random value; the application derives a Fernet key from it:

```powershell
$env:AI_CREDENTIAL_ENCRYPTION_KEY = 'replace-with-a-long-random-local-secret'
```

Create an admin user through a controlled database seed or administration procedure. Never expose this API to candidates.
