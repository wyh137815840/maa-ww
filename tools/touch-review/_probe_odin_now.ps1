$cfg = Get-Content (Join-Path $PSScriptRoot 'config.json') -Raw | ConvertFrom-Json
$adb = [string]$cfg.adb_path
$s = [string]$cfg.serial
& $adb -s $s shell wm size
& $adb -s $s shell wm density
& $adb -s $s shell dumpsys window displays 2>$null | Select-String 'init=|cur=|app=' | Select-Object -First 12
& $adb -s $s shell dumpsys activity activities 2>$null | Select-String 'mResumedActivity|topResumedActivity' | Select-Object -First 4
& $adb -s $s shell pidof com.kurogame.mingchao
