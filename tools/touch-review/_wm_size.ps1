$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
$serial = '127.0.0.1:16384'
& $adb connect $serial | Out-Null
& $adb -s $serial shell wm size
& $adb -s $serial shell wm density
