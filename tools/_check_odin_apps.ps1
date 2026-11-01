$ErrorActionPreference = "Continue"
$cfg = Get-Content "D:\git\maa-ww\tools\touch-review\config.json" -Raw | ConvertFrom-Json
$adb = $cfg.adb_path
$s = $cfg.serial
Write-Output "serial=$s"
& $adb connect $s
& $adb devices -l
& $adb -s $s shell getprop ro.product.model
Write-Output "--- packages ---"
& $adb -s $s shell pm list packages
Write-Output "--- maaww ---"
& $adb -s $s shell dumpsys package com.aliothmoon.maafw.maaww | Select-String "versionName|versionCode|enabled=" | Select-Object -First 8
