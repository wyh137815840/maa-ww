$ErrorActionPreference = 'Continue'
$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'

Write-Output '=== processes ==='
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -match 'MuMu|Nemu|clash|verge|mihomo|Wuthering|Client|ace|ACE' } |
  Select-Object Name, ProcessId |
  Format-Table -AutoSize

Write-Output '=== adb ==='
if (Test-Path $adb) {
  & $adb kill-server 2>$null
  Start-Sleep -Seconds 1
  & $adb start-server
  & $adb connect 127.0.0.1:16384
  & $adb connect 127.0.0.1:5555
  & $adb devices -l
  $devs = (& $adb devices) | Select-String "`tdevice$"
  foreach ($d in $devs) {
    $serial = ($d.ToString() -split '\s+')[0]
    Write-Output ("--- " + $serial + " ---")
    & $adb -s $serial shell wm size
    & $adb -s $serial shell getprop sys.boot_completed
    & $adb -s $serial shell getprop ro.build.version.release
    & $adb -s $serial shell "pm list packages | grep -iE 'kuro|ww|wuthering|ace|hypergryph|client'"
    & $adb -s $serial shell "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp' | head -n 5"
  }
} else {
  Write-Output 'adb missing'
}

Write-Output '=== proxy ==='
$ie = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
"ProxyEnable=$($ie.ProxyEnable) ProxyServer=$($ie.ProxyServer)"

Write-Output '=== clash tun/rules snippet ==='
$cv = 'C:\Users\Administrator\AppData\Roaming\io.github.clash-verge-rev.clash-verge-rev\clash-verge.yaml'
$vg = 'C:\Users\Administrator\AppData\Roaming\io.github.clash-verge-rev.clash-verge-rev\verge.yaml'
if (Test-Path $cv) {
  Select-String -Path $cv -Pattern 'tun:|enable:|MuMu|kurogame' | Select-Object -First 25
}
if (Test-Path $vg) {
  Select-String -Path $vg -Pattern 'enable_tun|enable_system_proxy|system_proxy_bypass'
}

Write-Output '=== adapters (hyper-v/mumu) ==='
Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -or $_.Name -match 'MuMu|VBox|Hyper|Clash|Meta|Wintun|tun' } |
  Select-Object Name, Status, MacAddress, LinkSpeed |
  Format-Table -AutoSize
