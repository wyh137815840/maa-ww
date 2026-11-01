$a = 'D:\leidian\LDPlayer14\adb.exe'
& $a start-server | Out-Null
& $a connect '127.0.0.1:5555'
& $a devices -l
& $a -s '127.0.0.1:5555' shell getprop ro.build.version.release
& $a -s '127.0.0.1:5555' shell wm size
& $a -s '127.0.0.1:5555' shell pidof com.kurogame.mingchao
