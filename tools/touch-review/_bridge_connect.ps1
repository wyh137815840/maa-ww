$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
Write-Output '=== ping ==='
ping -n 2 192.168.1.50
Write-Output '=== try adb ports ==='
foreach ($c in @('192.168.1.50:5555','192.168.1.50:5554','192.168.1.50:16416','192.168.1.50:16384')) {
  Write-Output ("-- " + $c)
  & $adb connect $c 2>&1 | Out-String
}
& $adb devices -l
$online = (& $adb devices) | Select-String "`tdevice$"
foreach ($d in $online) {
  $s = ($d.ToString() -split '\s+')[0]
  if ($s -notlike '192.168.1.50*') { continue }
  Write-Output ("=== " + $s)
  & $adb -s $s shell getprop ro.build.version.release
  & $adb -s $s shell wm size
  & $adb -s $s shell 'dumpsys SurfaceFlinger --display-id'
}
