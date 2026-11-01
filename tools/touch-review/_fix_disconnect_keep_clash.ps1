# Fix disconnect WITHOUT touching Clash system proxy (Cursor needs it).
$ErrorActionPreference = 'Continue'

Write-Host '=== kill WW launcher / tools (ok-ww: causes disconnect) ==='
foreach ($n in @('launcher-x64', 'launcher', 'WutheringWavesTool', 'Client-Win64-Shipping')) {
  Get-Process -Name $n -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "kill $($_.Name) pid=$($_.Id)"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
  }
}

$p = 'D:\Program Files\Netease\MuMuPlayer-12.0\vms\MuMuPlayer-15.0-1\configs\customer_config.json'
if (Test-Path $p) {
  $bak = "$p.bak_keepclash_$(Get-Date -Format yyyyMMdd_HHmmss)"
  Copy-Item $p $bak -Force
  $txt = [IO.File]::ReadAllText($p)
  $txt = $txt.Replace('"phone.mode.custom"', '"phone.mode.default"')
  # Prefer public DNS that works from emu (already pingable)
  $txt = $txt.Replace('"network_dns1": "192.168.1.1"', '"network_dns1": "223.5.5.5"')
  $txt = $txt.Replace('"dns1": "192.168.1.1"', '"dns1": "223.5.5.5"')
  $txt = $txt.Replace('"network_dns2": "8.8.8.8"', '"network_dns2": "114.114.114.114"')
  $txt = $txt.Replace('"dns2": "8.8.8.8"', '"dns2": "114.114.114.114"')
  [IO.File]::WriteAllText($p, $txt)
  Write-Host "patched phone=default dns=223.5.5.5/114 (bak $bak)"
}

# Clear any http proxy inside Android (Clash must NOT be set as emu proxy)
$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe'
& $adb -s 192.168.1.50:5555 shell 'settings delete global http_proxy; settings delete global global_http_proxy_host; settings delete global global_http_proxy_port; settings put global private_dns_mode off' | Out-Host

Write-Host ''
Write-Host 'IMPORTANT: fully quit MuMu and reopen once so phone/DNS apply.'
Write-Host 'Do NOT open WutheringWaves PC launcher / WutheringWavesTool while using MuMu.'
Write-Host 'Clash system proxy left ON for Cursor.'
