$ErrorActionPreference = 'Continue'
Write-Host '=== MuMu DNS / phone / bridge ==='
$p = 'D:\Program Files\Netease\MuMuPlayer-12.0\vms\MuMuPlayer-15.0-1\configs\customer_config.json'
Select-String -Path $p -Pattern '"dns1"|"dns2"|"network_dns1"|"bridge_mode"|"phone.mode'

Write-Host '=== processes ==='
Get-CimInstance Win32_Process | Where-Object {
  $_.Name -match 'launcher|WutheringWavesTool|Client-Win64|MuMuNxMain|clash-verge|verge-mihomo'
} | Select-Object Name, ProcessId | Format-Table -AutoSize

Write-Host '=== WinINET proxy ==='
$reg = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
"ProxyEnable=$($reg.ProxyEnable) ProxyServer=$($reg.ProxyServer)"

Write-Host '=== verge flags ==='
Select-String -Path "$env:APPDATA\io.github.clash-verge-rev.clash-verge-rev\verge.yaml" -Pattern 'enable_system_proxy|enable_dns_settings|enable_tun'

$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe'
Write-Host '=== adb devices ==='
& $adb devices
Write-Host '=== emu net / proxy / resolve ==='
& $adb -s 192.168.1.50:5555 shell 'getprop | grep -iE "dns|proxy|dhcp"; echo ---; settings list global | grep -i proxy; echo ---; ping -c 1 -W 2 223.5.5.5; ping -c 1 -W 2 sdkapi.kurogame.com; ping -c 1 -W 2 180.188.20.97'
