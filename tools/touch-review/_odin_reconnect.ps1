# Reconnect AYN Odin3 WiFi ADB. Usage:
#   pwsh -File _odin_reconnect.ps1
#   pwsh -File _odin_reconnect.ps1 -Serial <ip:port>
param(
  [string]$Serial = '',
  [string]$Adb = 'D:\leidian\LDPlayer14\adb.exe'
)
$cfgPath = Join-Path $PSScriptRoot 'config.json'
$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
if (-not $Serial) { $Serial = [string]$cfg.serial }
if ($cfg.adb_path) { $Adb = [string]$cfg.adb_path }

Write-Output "adb=$Adb serial=$Serial"
& $Adb start-server | Out-Null
& $Adb connect $Serial
& $Adb devices -l
& $Adb -s $Serial shell getprop ro.product.model
& $Adb -s $Serial shell wm size
& $Adb -s $Serial shell dumpsys window displays 2>$null | Select-String 'init=|cur=|app=' | Select-Object -First 6
& $Adb -s $Serial shell pidof com.kurogame.mingchao
& $Adb -s $Serial shell dumpsys activity activities 2>$null | Select-String 'topResumedActivity|mResumedActivity' | Select-Object -First 4
