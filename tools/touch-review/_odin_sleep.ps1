# Turn off Odin screen after verification sessions.
$ErrorActionPreference = "Stop"
$cfgPath = Join-Path $PSScriptRoot "config.json"
$cfg = Get-Content -Raw -Path $cfgPath | ConvertFrom-Json
& $cfg.adb_path -s $cfg.serial shell input keyevent KEYCODE_SLEEP
Write-Output "KEYCODE_SLEEP -> $($cfg.serial)"
