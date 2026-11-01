$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
$s = '127.0.0.1:16416'
& $adb -s $s shell am start -n com.kurogame.mingchao/com.kurogame.client.ClientActivity
Start-Sleep -Seconds 3
& $adb -s $s shell "ps -A | grep -i kuro"
& $adb -s $s shell "dumpsys activity activities | grep -E 'mResumedActivity|topResumed' | head -n 5"
# check recent crash
$log = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\log\server\log\MuMuPlayer\log_0.txt'
Select-String -Path $log -Pattern 'on_app_crash|mingchao' | Select-Object -Last 8 | ForEach-Object { $_.Line }
