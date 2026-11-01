$adb = 'D:\leidian\LDPlayer14\adb.exe'
$serial = '192.168.1.3:41277'

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
