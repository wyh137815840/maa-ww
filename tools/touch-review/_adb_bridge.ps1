$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
foreach ($c in @('192.168.1.16:5555','192.168.1.16:16384','192.168.1.16:5554')) {
  Write-Output ("try " + $c)
  & $adb connect $c 2>&1 | Out-String | Write-Output
}
& $adb devices -l
$online = (& $adb devices) | Select-String "`tdevice$"
foreach ($d in $online) {
  $s = ($d.ToString() -split '\s+')[0]
  Write-Output ("--- " + $s)
  & $adb -s $s shell wm size
  & $adb -s $s shell getprop ro.product.model
  & $adb -s $s shell getprop ro.product.manufacturer
  & $adb -s $s shell "logcat -d -t 80 | grep -iE 'FATAL|AndroidRuntime|mingchao|kuro|crash'"
}
