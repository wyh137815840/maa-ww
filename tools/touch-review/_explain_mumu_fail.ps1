$ErrorActionPreference = 'Continue'
Write-Host '=== any launcher still running? ==='
Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'launcher|MuMuNx|Wuthering' } |
  Select-Object Name, ProcessId, ExecutablePath | Format-List

Write-Host '=== config + backups ==='
$dir = 'D:\Program Files\Netease\MuMuPlayer-12.0\vms\MuMuPlayer-15.0-1\configs'
Get-ChildItem $dir -Filter 'customer_config.json*' | Sort-Object LastWriteTime -Descending |
  Format-Table Name, LastWriteTime, Length -AutoSize

Write-Host '=== current key fields ==='
Select-String -Path "$dir\customer_config.json" -Pattern 'phone.mode|dns1|dns2|bridge_mode|network_dns'
