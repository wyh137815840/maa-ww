$ErrorActionPreference = 'Continue'
$adb = @(
  'D:\leidian\LDPlayer14\adb.exe',
  'C:\leidian\LDPlayer9\adb.exe',
  'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
) | Where-Object { Test-Path $_ } | Select-Object -First 1
$w = Get-Command adb -ErrorAction SilentlyContinue
if ($w) { $adb = $w.Source }
Write-Output "adb=$adb"

& $adb kill-server 2>$null | Out-Null
Start-Sleep -Milliseconds 300
& $adb start-server | Out-Null

# Collect candidate IPs: ARP + this host's LAN segments
$ips = [System.Collections.Generic.HashSet[string]]::new()
try {
  arp -a | ForEach-Object {
    if ($_ -match '(\d+\.\d+\.\d+\.\d+)') {
      $ip = $Matches[1]
      if ($ip -notmatch '^(224\.|239\.|255\.|0\.|127\.)') { [void]$ips.Add($ip) }
    }
  }
} catch {}

Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Where-Object { $_.IPAddress -notmatch '^(127\.|169\.254\.)' } |
  ForEach-Object {
    $parts = $_.IPAddress.Split('.')
    if ($parts.Length -eq 4) {
      $prefix = "$($parts[0]).$($parts[1]).$($parts[2])"
      # only add ARP-known in same subnet already; also try .1-.40 lightly? too slow — skip
      Write-Output ("local_if=" + $_.IPAddress + " prefix=" + $prefix)
    }
  }

Write-Output ("candidates=" + (($ips | Sort-Object) -join ', '))

# Wireless debugging often uses high ports; also classic 5555
$ports = @(5555, 55555)
# Also probe a few common wireless-debug ephemeral-ish ports seen on Android 11+
foreach ($p in 37000,37100,37200,37300,37400,37500,37600,37700,37800,37900,40000,41000,42000,44000,45000,45455) {
  $ports += $p
}

function Try-Connect([string]$target) {
  $job = Start-Job -ScriptBlock {
    param($a, $t)
    & $a connect $t 2>&1 | Out-String
  } -ArgumentList $adb, $target
  if (Wait-Job $job -Timeout 2) {
    $r = (Receive-Job $job | Out-String).Trim()
    Remove-Job $job -Force -ErrorAction SilentlyContinue
    return $r
  }
  Stop-Job $job -ErrorAction SilentlyContinue
  Remove-Job $job -Force -ErrorAction SilentlyContinue
  return 'timeout'
}

# Fast path: TCP connect probe then adb connect only if port open
function Port-Open([string]$ip, [int]$port) {
  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $iar = $client.BeginConnect($ip, $port, $null, $null)
    $ok = $iar.AsyncWaitHandle.WaitOne(250, $false)
    if (-not $ok) { $client.Close(); return $false }
    $client.EndConnect($iar) | Out-Null
    $client.Close()
    return $true
  } catch { return $false }
}

Write-Output '=== port scan (open only) ==='
$hits = @()
foreach ($ip in ($ips | Sort-Object)) {
  foreach ($port in 5555, 55555) {
    if (Port-Open $ip $port) {
      Write-Output "OPEN ${ip}:${port}"
      $hits += "${ip}:${port}"
    }
  }
}

# Broader high-port scan only on private LAN hosts that answered ping-ish via ARP
Write-Output '=== high-port quick scan (5555/55555 already done; sample wireless-debug) ==='
$high = @(37039, 37101, 37215, 37333, 38433, 39857, 40123, 41234, 42000, 43210, 44000, 45000, 45455, 45677, 47000, 48000, 49000)
foreach ($ip in ($ips | Sort-Object)) {
  if ($ip -match '\.255$|\.0$') { continue }
  foreach ($port in $high) {
    if (Port-Open $ip $port) {
      Write-Output "OPEN ${ip}:${port}"
      $hits += "${ip}:${port}"
    }
  }
}

Write-Output '=== adb connect open ports ==='
foreach ($t in ($hits | Select-Object -Unique)) {
  $r = Try-Connect $t
  Write-Output "$t => $r"
}

Write-Output '=== devices ==='
& $adb devices -l

$devs = (& $adb devices) | Select-String "`tdevice$"
foreach ($d in $devs) {
  $s = ($d.ToString() -split '\s+')[0]
  Write-Output "=== probe $s ==="
  & $adb -s $s shell getprop ro.product.model
  & $adb -s $s shell getprop ro.product.manufacturer
  & $adb -s $s shell getprop ro.product.brand
  & $adb -s $s shell getprop ro.product.device
  & $adb -s $s shell wm size
  & $adb -s $s shell getprop ro.build.version.release
  & $adb -s $s shell getprop ro.serialno
}
