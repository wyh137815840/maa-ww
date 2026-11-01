$ErrorActionPreference = 'Continue'
$conn = Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
  Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 1
  Write-Host "killed $($conn.OwningProcess)"
}
Start-Process -FilePath python -ArgumentList 'tools\touch-review\serve.py' -WorkingDirectory 'D:\git\maa-ww' -WindowStyle Minimized
Start-Sleep -Seconds 2
Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue |
  Select-Object -First 1 State, OwningProcess |
  Format-List
