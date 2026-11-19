# Upload the synthetic "Marcus" cross-source bundle to S3.
# Requires the sandbox AWS profile to be active (run updatesandbox.bat first).
# Usage:  powershell -ExecutionPolicy Bypass -File .\upload_marcus_bundle.ps1

$ErrorActionPreference = 'Stop'
$profileName = '304507007699_AWSPowerUserAccess'
$bucket = 'nyec-synthetic-data'
$prefix = 'demo-marcus'          # everything about Marcus lives here
$local  = Join-Path $PSScriptRoot 'marcus_bundle'

if (-not (Test-Path $local)) { throw "marcus_bundle not found. Run: python build_marcus_bundle.py" }

# fail fast if the profile isn't present
aws configure list --profile $profileName | Out-Null

aws s3 cp $local "s3://$bucket/$prefix/" --recursive `
    --profile $profileName `
    --exclude "*" --include "*.xml" --include "*.hl7" --include "*.csv" --include "*.md"

Write-Host ""
Write-Host "Uploaded. Files for Julie:" -ForegroundColor Green
aws s3 ls "s3://$bucket/$prefix/" --recursive --profile $profileName
Write-Host ""
Write-Host "Base path:  s3://$bucket/$prefix/" -ForegroundColor Cyan
Write-Host "Start here: s3://$bucket/$prefix/README.md" -ForegroundColor Cyan
