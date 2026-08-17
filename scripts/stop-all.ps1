$ErrorActionPreference = "Stop"
Write-Host "=== IARH FULL DOCKER STOP ===" -ForegroundColor Cyan
docker compose down
Write-Host "Services arretes." -ForegroundColor Green
