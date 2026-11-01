$adb = 'D:\leidian\LDPlayer14\adb.exe'
$s = '192.168.1.3:41277'
& $adb -s $s shell wm size
& $adb -s $s shell wm density
& $adb -s $s shell dumpsys window displays 2>$null | Select-String 'init=|cur=|app=' | Select-Object -First 12
& $adb -s $s shell dumpsys activity activities 2>$null | Select-String 'mResumedActivity|topResumedActivity' | Select-Object -First 4
& $adb -s $s shell pidof com.kurogame.mingchao
