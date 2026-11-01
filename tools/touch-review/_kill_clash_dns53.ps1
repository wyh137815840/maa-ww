$ErrorActionPreference = 'Continue'
$vergeDir = Join-Path $env:APPDATA 'io.github.clash-verge-rev.clash-verge-rev'
$clashYaml = Join-Path $vergeDir 'clash-verge.yaml'

function Disable-DnsListen([string]$Path) {
  if (-not (Test-Path $Path)) { return }
  $txt = [IO.File]::ReadAllText($Path)
  $orig = $txt
  # Turn off DNS module entirely for stability while labeling / gaming on emu
  $txt = [regex]::Replace($txt, '(?m)^dns:\r?\n(?:[ \t].*\r?\n)*', @"
dns:
  enable: false
  ipv6: false
  # listen disabled — was binding :53 and poisoning MuMu/game sessions
  enhanced-mode: redir-host
  nameserver:
  - 223.5.5.5
  - 8.8.8.8

"@)
  if ($txt -eq $orig) {
    # fallback line edits
    $txt = [regex]::Replace($txt, '(?m)^(\s*)enable:\s*true\s*$', '${1}enable: false', 1)
    $txt = [regex]::Replace($txt, '(?m)^(\s*)listen:\s*:53\s*$', '${1}# listen removed')
    $txt = [regex]::Replace($txt, '(?m)^(\s*)enhanced-mode:\s*fake-ip\s*$', '${1}enhanced-mode: redir-host')
  }
  if ($txt -ne $orig) {
    [IO.File]::WriteAllText($Path, $txt)
    Write-Host "rewrote dns block in $Path"
  } else {
    Write-Host "no dns change applied to $Path"
  }
}

Disable-DnsListen $clashYaml

# Also patch any profile that injects dns
Get-ChildItem $vergeDir -Filter '*.yaml' -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match 'clash|config|profile' } |
  ForEach-Object {
    $c = [IO.File]::ReadAllText($_.FullName)
    if ($c -match '(?m)^dns:\s*$' -and $c -match 'listen:\s*:53') {
      Write-Host "also has :53 -> $($_.FullName)"
    }
  }

# Try external controller via named pipe is hard; use HTTP if secret known
$cfg = Get-Content (Join-Path $vergeDir 'verge.yaml') -Raw
# common secrets / ports in verge
if ($cfg -match 'verge_mixed_port:\s*(\d+)') { Write-Host "mixed=$($Matches[1])" }
if ($cfg -match 'clash_core:\s*(\S+)') { Write-Host "core=$($Matches[1])" }

# Force-reload by killing only mihomo; verge will respawn — then immediately rewrite again
$mihomo = Get-Process verge-mihomo -ErrorAction SilentlyContinue
if ($mihomo) {
  Write-Host "kill mihomo $($mihomo.Id)"
  Stop-Process -Id $mihomo.Id -Force
}
Start-Sleep -Seconds 3
Disable-DnsListen $clashYaml

# If Clash Verge auto-restores fake-ip from profile_dns_settings, clear those flags again
$verge = Join-Path $vergeDir 'verge.yaml'
$vt = [IO.File]::ReadAllText($verge)
$vt2 = [regex]::Replace($vt, '(?m)^enable_dns_settings:\s*true\s*$', 'enable_dns_settings: false')
$vt2 = [regex]::Replace($vt2, '(?m)^enable_system_proxy:\s*true\s*$', 'enable_system_proxy: false')
if ($vt2 -ne $vt) { [IO.File]::WriteAllText($verge, $vt2); Write-Host 're-asserted verge dns/proxy off' }

Start-Sleep -Seconds 4
Write-Host '=== :53 ==='
Get-NetUDPEndpoint -LocalPort 53 -ErrorAction SilentlyContinue | ForEach-Object {
  $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
  "{0} pid={1} {2}" -f $_.LocalAddress, $_.OwningProcess, $p.ProcessName
}
Select-String -Path $clashYaml -Pattern 'enable:|listen:|enhanced-mode:' | Select-Object -First 15
