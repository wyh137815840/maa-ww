$ErrorActionPreference = 'Continue'
Write-Output '=== proxy ==='
$ie = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
"ProxyEnable=$($ie.ProxyEnable) ProxyServer=$($ie.ProxyServer) Override=$($ie.ProxyOverride)"

Write-Output '=== clash verge flags ==='
$vg = 'C:\Users\Administrator\AppData\Roaming\io.github.clash-verge-rev.clash-verge-rev\verge.yaml'
Select-String -Path $vg -Pattern 'enable_tun|enable_system_proxy|system_proxy_bypass|mixed' | ForEach-Object { $_.Line }

Write-Output '=== mumu network / phone ==='
$cfgs = @(
  'D:\Program Files\Netease\MuMuPlayer-12.0\vms\MuMuPlayer-15.0-1\configs\customer_config.json',
  'D:\Program Files\Netease\MuMuPlayer-12.0\vms\MuMuPlayer-12.0-0\configs\customer_config.json'
)
foreach ($c in $cfgs) {
  if (-not (Test-Path $c)) { continue }
  Write-Output ("-- " + $c)
  $j = Get-Content $c -Raw | ConvertFrom-Json
  $s = $j.setting
  "bridge=$($s.network_setting.bridge_mode) phone=$($s.phone.brand) $($s.phone.model) mode=$($s.phone.mode.choose) render=$($s.render.mode.choose)/$($s.render.mode.highperformance)"
}

Write-Output '=== adb ==='
$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
& $adb devices -l
foreach ($s in @('192.168.1.50:5555','127.0.0.1:16416')) {
  $r = & $adb -s $s shell echo ok 2>&1
  Write-Output ("$s -> $r")
}

Write-Output '=== route to common game CDN (direct?) ==='
# sample resolve
nslookup api.kurogame.com 2>$null | Select-Object -First 12
Test-NetConnection api.kurogame.com -Port 443 -WarningAction SilentlyContinue |
  Select-Object ComputerName, RemoteAddress, TcpTestSucceeded | Format-List
