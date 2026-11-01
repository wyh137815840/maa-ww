# Restore Clash for Cursor/system proxy; do NOT leave Cursor offline.
# Keep game path: MuMu PROCESS DIRECT + kuro DIRECT already in rules.
# Avoid killing Clash or clearing WinINET permanently.

$ErrorActionPreference = 'Continue'
$vergeDir = Join-Path $env:APPDATA 'io.github.clash-verge-rev.clash-verge-rev'
$verge = Join-Path $vergeDir 'verge.yaml'

# Re-enable system proxy so Cursor can reach network via Clash mixed port
if (Test-Path $verge) {
  $txt = [IO.File]::ReadAllText($verge)
  $txt2 = [regex]::Replace($txt, '(?m)^enable_system_proxy:\s*false\s*$', 'enable_system_proxy: true')
  # Keep DNS settings OFF — host DNS hijack was the disconnect culprit; Cursor uses HTTP proxy not :53
  $txt2 = [regex]::Replace($txt2, '(?m)^enable_dns_settings:\s*true\s*$', 'enable_dns_settings: false')
  $txt2 = [regex]::Replace($txt2, '(?m)^enable_tun_mode:\s*true\s*$', 'enable_tun_mode: false')
  if ($txt2 -ne $txt) {
    [IO.File]::WriteAllText($verge, $txt2)
    Write-Host 'verge.yaml: system_proxy=true, dns_settings=false, tun=false'
  } else {
    Write-Host 'verge.yaml already desired or pattern miss'
    Select-String -Path $verge -Pattern 'enable_system_proxy|enable_dns_settings|enable_tun'
  }
}

# Ensure clash-verge is running
$cv = Get-Process clash-verge -ErrorAction SilentlyContinue
$exe = 'C:\Program Files\Clash Verge\clash-verge.exe'
if (-not $cv) {
  if (Test-Path $exe) {
    Start-Process $exe
    Write-Host "started $exe"
    Start-Sleep -Seconds 4
  } else {
    Write-Host 'clash-verge.exe missing'
  }
} else {
  Write-Host "clash-verge already pid=$($cv.Id)"
}

# Re-assert WinINET proxy to Clash mixed port (7897 from earlier diag)
$reg = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
Set-ItemProperty -Path $reg -Name ProxyEnable -Value 1
Set-ItemProperty -Path $reg -Name ProxyServer -Value '127.0.0.1:7897'
# Keep LAN/emulator bypass
$bypass = 'localhost;127.*;192.168.*;10.*;172.16.*;172.17.*;172.18.*;172.19.*;172.20.*;172.21.*;172.22.*;172.23.*;172.24.*;172.25.*;172.26.*;172.27.*;172.28.*;172.29.*;172.30.*;172.31.*;<local>'
Set-ItemProperty -Path $reg -Name ProxyOverride -Value $bypass
Write-Host 'WinINET ProxyEnable=1 ProxyServer=127.0.0.1:7897'

# Quick connectivity via proxy
try {
  $r = Invoke-WebRequest -Uri 'https://www.baidu.com' -UseBasicParsing -TimeoutSec 8
  Write-Host "baidu via system proxy: $($r.StatusCode)"
} catch {
  Write-Host "baidu check: $_"
}

Write-Host 'ProxyEnable=' (Get-ItemProperty $reg).ProxyEnable
Write-Host 'ProxyServer=' (Get-ItemProperty $reg).ProxyServer
Get-Process clash-verge,verge-mihomo -ErrorAction SilentlyContinue | Format-Table Name,Id -AutoSize
