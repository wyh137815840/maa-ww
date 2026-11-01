$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
$cfg = 'D:\Program Files\Netease\MuMuPlayer-12.0\vms\MuMuPlayer-12.0-0\configs\customer_config.json'
$log = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\log\server\log\MuMuPlayer\log_0.txt'

Write-Output '=== customer phone / network / render / resolution ==='
if (Test-Path $cfg) {
  $j = Get-Content $cfg -Raw | ConvertFrom-Json
  $s = $j.setting
  "phone.mode=$($s.phone.mode.choose) model=$($s.phone.model) brand=$($s.phone.brand) manufacturer=$($s.phone.manufacturer)"
  "bridge=$($s.network_setting.bridge_mode) card=$($s.network_setting.current_bridge_card)"
  "render.choose=$($s.render.mode.choose) hp=$($s.render.mode.highperformance) stable=$($s.render.mode.stable)"
  "resolution=$($s.resolution.current) resMode=$($s.resolution.mode.choose)"
  "adb=$($s.other_setting.adb_debug_setting.mode.choose)"
}

Write-Output '=== adb 16384 ==='
& $adb connect 127.0.0.1:16384 2>&1 | Out-String
& $adb devices
$devs = (& $adb devices) | Select-String "`tdevice$"
foreach ($d in $devs) {
  $s = ($d.ToString() -split '\s+')[0]
  & $adb -s $s shell getprop ro.build.version.release
  & $adb -s $s shell getprop ro.product.model
  & $adb -s $s shell wm size
}

Write-Output '=== latest crash lines ==='
if (Test-Path $log) {
  Select-String -Path $log -Pattern 'on_app_crash|mingchao|Android' |
    Select-Object -Last 15 |
    ForEach-Object { $_.Line }
}
