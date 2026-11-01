$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
$s = '127.0.0.1:16416'
& $adb connect $s | Out-Null
Write-Output '=== packages ==='
& $adb -s $s shell "pm list packages | grep -iE 'kuro|mingchao|wuther'"
Write-Output '=== launch ==='
# official CN package commonly com.kurogame.mingchao
& $adb -s $s shell monkey -p com.kurogame.mingchao -c android.intent.category.LAUNCHER 1
Start-Sleep -Seconds 8
& $adb -s $s shell "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp' | head -n 4"
Set-Location D:\git\maa-ww
python tools\touch-review\capture.py --label after-launch-ww
