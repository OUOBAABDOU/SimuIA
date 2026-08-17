$ErrorActionPreference = "Stop"
Write-Host "=== IARH FULL DOCKER START ===" -ForegroundColor Cyan

docker compose config --quiet
if ($LASTEXITCODE -ne 0) { throw "docker compose config a echoue." }

docker compose up --build -d
if ($LASTEXITCODE -ne 0) { throw "Le demarrage Docker a echoue." }

Write-Host "=== ATTENTE DU READINESS FASTAPI ===" -ForegroundColor Cyan
$ready = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8000/api/v1/health/ready" -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch {}
    Start-Sleep -Seconds 2
}
if (-not $ready) {
    docker compose ps
    docker compose logs --tail=80 backend
    throw "FastAPI n'est pas ready apres 60 secondes."
}

Write-Host "=== SERVICES ===" -ForegroundColor Cyan
docker compose ps

Write-Host "=== CHECKS ===" -ForegroundColor Green
Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:8000/api/v1/health/ready" -TimeoutSec 5 | Select-Object -ExpandProperty Content
Write-Host "Frontend Flutter Web : http://localhost"
Write-Host "FastAPI Swagger      : http://localhost:8000/docs"
Write-Host "FastAPI Readiness    : http://localhost:8000/api/v1/health/ready"
Write-Host "MinIO Console        : http://localhost:9001"
Write-Host "LiveKit              : ws://localhost:7880"
