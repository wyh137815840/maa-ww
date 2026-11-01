# Wake + unlock Odin with PIN (联调专用)
$ErrorActionPreference = "Stop"
$cfg = Get-Content (Join-Path $PSScriptRoot "touch-review\config.json") -Raw | ConvertFrom-Json
$adb = $cfg.adb_path
$s = $cfg.serial
& $adb connect $s | Out-Host
& $adb -s $s shell input keyevent KEYCODE_WAKEUP
Start-Sleep -Milliseconds 400
& $adb -s $s shell input keyevent 82   # unlock/menu
Start-Sleep -Milliseconds 300
& $adb -s $s shell input text 753698
Start-Sleep -Milliseconds 200
& $adb -s $s shell input keyevent KEYCODE_ENTER
Write-Output "unlocked"
