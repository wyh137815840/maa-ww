$ErrorActionPreference = 'Stop'
$headers = @{ Authorization = 'Bearer set-your-secret' }
try {
  $v = Invoke-RestMethod -Uri 'http://127.0.0.1:9097/version' -Headers $headers
  Write-Output ("clash=" + $v.version)
} catch {
  Write-Output ("api_error=" + $_.Exception.Message)
  exit 1
}

# Ask verge-mihomo to reload current config path (Clash Verge may need UI refresh for profile merge)
try {
  Invoke-RestMethod -Method Put -Uri 'http://127.0.0.1:9097/configs?force=true' -Headers $headers -ContentType 'application/json' -Body '{}'
  Write-Output 'reload_ok'
} catch {
  Write-Output ("reload_error=" + $_.Exception.Message)
}
