$cfg = Get-Content (Join-Path $PSScriptRoot 'config.json') -Raw | ConvertFrom-Json
$adb = [string]$cfg.adb_path
$serial = [string]$cfg.serial

& $adb connect $serial
& $adb devices -l

Write-Output "=== probe $serial ==="
& $adb -s $serial shell getprop ro.product.model
& $adb -s $serial shell getprop ro.product.manufacturer
& $adb -s $serial shell getprop ro.product.brand
& $adb -s $serial shell getprop ro.product.device
& $adb -s $serial shell wm size
& $adb -s $serial shell getprop ro.build.version.release
& $adb -s $serial shell pidof com.kurogame.mingchao
