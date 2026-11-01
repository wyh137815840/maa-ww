$ErrorActionPreference = 'Continue'
$adbCandidates = @(
  'D:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe',
  'D:\Program Files\Netease\MuMuPlayer-12.0\nx_device\12.0\shell\adb.exe'
)
$adb = $adbCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $adb) {
  $cmd = Get-Command adb -ErrorAction SilentlyContinue
  if ($cmd) { $adb = $cmd.Source }
}
Write-Host "adb=$adb"

# Kill Kuro / WW launcher that ok-ww documents as disconnect cause
foreach ($n in @('launcher-x64', 'launcher', 'Client-Win64-Shipping', 'WutheringWavesTool')) {
  Get-Process -Name $n -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "kill $($_.Name) pid=$($_.Id)"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
  }
}
# Keep MuMu game; only kill Windows launcher/tool helpers if any
# Do NOT kill MuMuNx*

if ($adb) {
  & $adb connect 192.168.1.50:5555 | Out-Host
  & $adb -s 192.168.1.50:5555 shell getprop net.dns1 | ForEach-Object { Write-Host "dns1=$_" }
  & $adb -s 192.168.1.50:5555 shell getprop net.dns2 | ForEach-Object { Write-Host "dns2=$_" }
  & $adb -s 192.168.1.50:5555 shell 'getprop | grep -i dns' | Out-Host
  # Try force DNS on running instance (may need root / may not stick)
  & $adb -s 192.168.1.50:5555 shell 'settings put global private_dns_mode off' | Out-Host
  & $adb -s 192.168.1.50:5555 shell 'ndc resolver setnetdns eth0 "" 192.168.1.1 8.8.8.8' | Out-Host
  & $adb -s 192.168.1.50:5555 shell 'ndc resolver setnetdns wlan0 "" 192.168.1.1 8.8.8.8' | Out-Host
  & $adb -s 192.168.1.50:5555 shell 'getprop net.dns1; getprop net.dns2; ping -c 1 -W 2 8.8.8.8; ping -c 1 -W 2 192.168.1.1' | Out-Host
}

Write-Host '=== resolve via DoH-ish curl ==='
try {
  $r = Invoke-RestMethod -Uri 'https://dns.alidns.com/resolve?name=hkrpg.mihoyo.com&type=A' -TimeoutSec 5
  Write-Host ("alidns selftest: " + ($r | ConvertTo-Json -Compress))
} catch { Write-Host "alidns fail $_" }
foreach ($d in @(
  'api.kurogame.com',
  'gface.kurogame.com',
  'aki-game.com',
  'www.kurogames.com',
  'sdkapi.kurogame.com',
  'prod-alicdn-sdkserver.kurogame.com'
)) {
  try {
    $r = Invoke-RestMethod -Uri ("https://dns.alidns.com/resolve?name={0}&type=A" -f $d) -TimeoutSec 5
    Write-Host ("{0}: {1}" -f $d, ($r | ConvertTo-Json -Compress))
  } catch {
    Write-Host ("{0}: FAIL {1}" -f $d, $_)
  }
}
