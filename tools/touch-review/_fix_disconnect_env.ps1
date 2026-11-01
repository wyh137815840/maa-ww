# Fix MuMu + Clash env that causes Kuro "连接已断开"
$ErrorActionPreference = 'Stop'

function Patch-TextFile([string]$Path, [hashtable]$Replacements) {
  if (-not (Test-Path $Path)) { Write-Host "skip missing $Path"; return }
  $bak = "$Path.bak_disconnect_$(Get-Date -Format yyyyMMdd_HHmmss)"
  Copy-Item $Path $bak -Force
  $txt = [IO.File]::ReadAllText($Path)
  foreach ($k in $Replacements.Keys) {
    $txt = $txt.Replace($k, [string]$Replacements[$k])
  }
  [IO.File]::WriteAllText($Path, $txt)
  Write-Host "patched $Path (bak $bak)"
}

$mumuCfgs = @(
  'D:\Program Files\Netease\MuMuPlayer-12.0\vms\MuMuPlayer-15.0-1\configs\customer_config.json',
  'D:\Program Files\Netease\MuMuPlayer-12.0\vms\MuMuPlayer-12.0-0\configs\customer_config.json'
)

foreach ($p in $mumuCfgs) {
  Patch-TextFile $p @{
    '"network_dns1": "144.144.144.144"' = '"network_dns1": "192.168.1.1"'
    '"dns1": "144.144.144.144"' = '"dns1": "192.168.1.1"'
    '"phone.mode.custom"' = '"phone.mode.default"'
  }
}

$verge = Join-Path $env:APPDATA 'io.github.clash-verge-rev.clash-verge-rev\verge.yaml'
if (Test-Path $verge) {
  $bak2 = "$verge.bak_disconnect_$(Get-Date -Format yyyyMMdd_HHmmss)"
  Copy-Item $verge $bak2 -Force
  $txt = [IO.File]::ReadAllText($verge)
  $txt = [regex]::Replace($txt, '(?m)^enable_system_proxy:\s*true\s*$', 'enable_system_proxy: false')
  $txt = [regex]::Replace($txt, '(?m)^enable_dns_settings:\s*true\s*$', 'enable_dns_settings: false')
  $txt = [regex]::Replace($txt, '(?m)^enable_tun_mode:\s*true\s*$', 'enable_tun_mode: false')
  [IO.File]::WriteAllText($verge, $txt)
  Write-Host "patched verge.yaml system_proxy/dns/tun off (bak $bak2)"
}

$reg = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
Set-ItemProperty -Path $reg -Name ProxyEnable -Value 0
Write-Host 'WinINET ProxyEnable=0'

Write-Host ''
Write-Host 'Done. Restart MuMu so bridge applies new DNS, then re-login.'
