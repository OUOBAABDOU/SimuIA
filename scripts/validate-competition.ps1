param(
  [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$ErrorActionPreference = 'Stop'
$required = @(
  'LICENSE',
  'COMPETITION_SUBMISSION.md',
  'docs/DEVPOST_SUBMISSION_EN.md',
  'docs/TEST_INSTRUCTIONS_EN.md',
  'docs/SUBMISSION_EVIDENCE_TEMPLATE_EN.md',
  'docs/THIRD_PARTY_LICENSES.md',
  'cloudbuild.yaml'
)

foreach ($relative in $required) {
  $path = Join-Path $Root $relative
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    throw "Missing competition artifact: $relative"
  }
}

$forbidden = @('sk-', 'AIza')
foreach ($relative in @('README.md', 'COMPETITION_SUBMISSION.md', 'cloudbuild.yaml')) {
  $content = Get-Content -LiteralPath (Join-Path $Root $relative) -Raw -Encoding utf8
  foreach ($marker in $forbidden) {
    if ($content -match [regex]::Escape($marker)) {
      throw "Possible credential marker found in $relative"
    }
  }
}

Write-Output 'Competition package structure and secret-marker checks passed.'
Write-Output 'Personal evidence, eligibility, deployment and Devpost fields still require completion.'
