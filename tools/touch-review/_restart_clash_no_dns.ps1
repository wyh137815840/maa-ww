$ErrorActionPreference = 'Continue'
$vergeDir = Join-Path $env:APPDATA 'io.github.clash-verge-rev.clash-verge-rev'
$clashYaml = Join-Path $vergeDir 'clash-verge.yaml'

# Soften DNS hijack in the runtime config: stop listening on :53 and leave fake-ip
if (Test-Path $clashYaml) {
  $bak = "$clashYaml.bak_nodns_$(Get-Date -Format yyyyMMdd_HHmmss)"
  Copy-Item $clashYaml $bak -Force
  $txt = [IO.File]::ReadAllText($clashYaml)
  # disable dns listen bind (keep dns section otherwise intact for when user re-enables)
  $txt = [regex]::Replace($txt, '(?m)^(\s*)listen:\s*:53\s*$', '${1}# listen: :53  # disabled: was hijacking host DNS')
  $txt = [regex]::Replace($txt, '(?m)^(\s*)enhanced-mode:\s*fake-ip\s*$', '${1}enhanced-mode: redir-host')
  [IO.File]::WriteAllText($clashYaml, $txt)
  Write-Host "patched clash-verge.yaml (bak $bak)"
}

# Restart Clash Verge so it drops :53
Get-Process clash-verge,verge-mihomo -ErrorAction SilentlyContinue | ForEach-Object {
  Write-Host "stop $($_.Name) $($_.Id)"
  Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2

$exe = @(
  "$env:LOCALAPPDATA\Programs\Clash Verge\clash-verge.exe",
  "$env:LOCALAPPDATA\Clash Verge\clash-verge.exe",
  'C:\Program Files\Clash Verge\clash-verge.exe'
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $exe) {
  $p = Get-CimInstance Win32_Process -Filter "Name='clash-verge.exe'" -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($p -and $p.ExecutablePath) { $exe = $p.ExecutablePath }
  # try locate from uninstall / shortcut
  $guess = Get-ChildItem -Path "$env:LOCALAPPDATA\Programs","C:\Program Files","D:\Program Files" -Filter 'clash-verge.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($guess) { $exe = $guess.FullName }
}

if ($exe) {
  Write-Host "start $exe"
  Start-Process -FilePath $exe
  Start-Sleep -Seconds 5
} else {
  Write-Host 'clash-verge.exe not found; start it manually from tray'
}

Start-Sleep -Seconds 2
Write-Host '=== :53 owners after restart ==='
Get-NetUDPEndpoint -LocalPort 53 -ErrorAction SilentlyContinue | ForEach-Object {
  $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
  "{0} pid={1} {2}" -f $_.LocalAddress, $_.OwningProcess, $p.ProcessName
}
Write-Host 'ProxyEnable=' (Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings').ProxyEnable
# force proxy off again after clash restart
Set-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -Name ProxyEnable -Value 0
