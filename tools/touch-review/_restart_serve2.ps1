$ErrorActionPreference = 'Continue'
Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -and ($_.CommandLine -like '*touch-review*serve.py*')
} | ForEach-Object {
  Write-Host "kill $($_.ProcessId)"
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 1
$proc = Start-Process -FilePath 'python' -ArgumentList 'tools\touch-review\serve.py' -WorkingDirectory 'D:\git\maa-ww' -PassThru -WindowStyle Minimized
Write-Host "started pid=$($proc.Id)"
Start-Sleep -Seconds 2
try {
  $r = Invoke-WebRequest 'http://127.0.0.1:8765/api/list' -UseBasicParsing -TimeoutSec 5
  Write-Host "api=$($r.StatusCode) len=$($r.Content.Length)"
  $j = $r.Content | ConvertFrom-Json
  Write-Host "cards=$($j.cards.Count) first_status=$($j.cards[0].status)"
} catch {
  Write-Host "api fail: $_"
}
