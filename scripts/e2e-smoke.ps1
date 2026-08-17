$ErrorActionPreference = 'Stop'

$api = if ($env:E2E_API_URL) { $env:E2E_API_URL.TrimEnd('/') } else { 'http://127.0.0.1:8000' }
$email = "e2e-$([guid]::NewGuid().ToString('N'))@example.com"
$password = "E2E-$([guid]::NewGuid().ToString('N'))-Aa1!"
$headers = $null

function Invoke-Json($method, $path, $body = $null, $requestHeaders = $null) {
  $params = @{ Uri = "$api$path"; Method = $method; UseBasicParsing = $true; TimeoutSec = 20 }
  if ($body -ne $null) { $params.ContentType = 'application/json'; $params.Body = ($body | ConvertTo-Json -Depth 8) }
  if ($requestHeaders -ne $null) { $params.Headers = $requestHeaders }
  Invoke-RestMethod @params
}

try {
  $null = Invoke-Json POST '/api/v1/auth/register' @{
    email=$email; password=$password; first_name='E2E'; last_name='Smoke'; domain='Engineering'; target_role='Developer'
  }
  $login = Invoke-Json POST '/api/v1/auth/login' @{ email=$email; password=$password }
  $headers = @{ Authorization = "Bearer $($login.access_token)" }
  $simulation = Invoke-Json POST '/api/v1/simulations' @{ category='entretien_embauche'; sector='Engineering'; role='Developer'; experience_level='intermediate'; interview_style='structured'; mode='text'; total_questions=1 } $headers
  $interview = Invoke-Json POST '/api/v1/interviews' @{ simulation_id=$simulation.id } $headers
  $null = Invoke-Json POST "/api/v1/interviews/$($interview.id)/start" $null $headers
  $question = Invoke-Json GET "/api/v1/interviews/$($interview.id)/current-question" $null $headers
  $null = Invoke-Json POST "/api/v1/interviews/$($interview.id)/questions/$($question.id)/answer" @{ answer_type='TEXT'; text='A controlled E2E answer.' } $headers
  $finished = Invoke-Json POST "/api/v1/interviews/$($interview.id)/finish" $null $headers
  if ($finished.status -notin @('EVALUATING','PROCESSING','COMPLETED')) { throw "Unexpected final status: $($finished.status)" }
  Write-Output "E2E smoke passed for $email"
} finally {
  if ($headers -ne $null) {
    try { Invoke-RestMethod -Uri "$api/api/v1/auth/me/data" -Method Delete -Headers $headers -UseBasicParsing -TimeoutSec 20 | Out-Null } catch { Write-Warning "E2E cleanup failed for ${email}: $($_.Exception.Message)" }
  }
}
