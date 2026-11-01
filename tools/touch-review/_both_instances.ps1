$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
foreach ($p in @('16384','16416')) {
  Write-Output ("==== " + $p + " ====")
  & $adb connect "127.0.0.1:$p" 2>&1 | Out-String
}
& $adb devices -l
$log = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\log\server\log\MuMuPlayer\log_0.txt'
Select-String -Path $log -Pattern 'on_app_crash|on_app_launch.*mingchao|Set current app' |
  Select-Object -Last 20 | ForEach-Object { $_.Line }
