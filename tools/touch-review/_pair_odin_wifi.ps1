$adb = @(
  'D:\leidian\LDPlayer14\adb.exe',
  'C:\leidian\LDPlayer9\adb.exe',
  'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
) | Where-Object { Test-Path $_ } | Select-Object -First 1
$w = Get-Command adb -ErrorAction SilentlyContinue
if ($w) { $adb = $w.Source }
Write-Output "adb=$adb"

$hostPort = '192.168.1.3:38147'
$code = '260701'

& $adb start-server | Out-Null

Write-Output "=== pair $hostPort ==="
# Modern adb: adb pair host:port CODE
$pairOut = & $adb pair $hostPort $code 2>&1 | Out-String
Write-Output $pairOut.Trim()

Write-Output "=== connect $hostPort ==="
$connOut = & $adb connect $hostPort 2>&1 | Out-String
Write-Output $connOut.Trim()

Write-Output '=== devices ==='
& $adb devices -l

$devs = (& $adb devices) | Select-String "`tdevice$"
foreach ($d in $devs) {
  $s = ($d.ToString() -split '\s+')[0]
  Write-Output "=== probe $s ==="
  & $adb -s $s shell getprop ro.product.model
  & $adb -s $s shell getprop ro.product.manufacturer
  & $adb -s $s shell getprop ro.product.brand
  & $adb -s $s shell wm size
  & $adb -s $s shell getprop ro.build.version.release
  & $adb -s $s shell pidof com.kurogame.mingchao
}
