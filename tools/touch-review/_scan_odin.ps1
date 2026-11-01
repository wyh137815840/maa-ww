$adbs = @(
  'D:\leidian\LDPlayer14\adb.exe',
  'C:\leidian\LDPlayer9\adb.exe',
  'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
)
$adb = $adbs | Where-Object { Test-Path $_ } | Select-Object -First 1
$w = Get-Command adb -ErrorAction SilentlyContinue
if ($w) { $adb = $w.Source }
Write-Output "adb=$adb"

& $adb kill-server 2>$null | Out-Null
Start-Sleep -Milliseconds 400
& $adb start-server | Out-Null

Write-Output '=== usb / all devices ==='
& $adb devices -l

Write-Output '=== listening ports (possible wireless debug) ==='
try {
  Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object {
      $_.LocalPort -in 5555,5556,5557,5037,55555,45455 -or
      ($_.LocalPort -ge 37000 -and $_.LocalPort -le 38000)
    } |
    Select-Object LocalAddress, LocalPort -Unique |
    Format-Table | Out-String | Write-Output
} catch {}

Write-Output '=== USB devices (WMI) ==='
Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
  Where-Object { $_.FriendlyName -match 'ADB|Android|Odin|AYN|Composite|MTP|增量' } |
  Select-Object Status, Class, FriendlyName |
  Format-Table -AutoSize | Out-String | Write-Output

Write-Output '=== try common wireless endpoints ==='
# User LAN; try gateway-ish and known ranges lightly via arp
$ips = @()
try {
  arp -a | ForEach-Object {
    if ($_ -match '(\d+\.\d+\.\d+\.\d+)') { $ips += $Matches[1] }
  }
} catch {}
$ips = $ips | Where-Object { $_ -notmatch '^(224\.|239\.|255\.|0\.|127\.)' } | Select-Object -Unique
Write-Output ("arp hosts: " + ($ips -join ', '))

foreach ($ip in $ips) {
  foreach ($port in 5555, 55555) {
    $c = "${ip}:${port}"
    $job = Start-Job -ScriptBlock {
      param($a, $t)
      & $a connect $t 2>&1 | Out-String
    } -ArgumentList $adb, $c
    if (Wait-Job $job -Timeout 2) {
      $r = (Receive-Job $job | Out-String).Trim()
      Remove-Job $job -Force -ErrorAction SilentlyContinue
      if ($r -match 'connected|already') { Write-Output "HIT $c :: $r" }
    } else {
      Stop-Job $job -ErrorAction SilentlyContinue
      Remove-Job $job -Force -ErrorAction SilentlyContinue
    }
  }
}

Write-Output '=== devices after scan ==='
& $adb devices -l

$devs = (& $adb devices) | Select-String "`tdevice$"
foreach ($d in $devs) {
  $s = ($d.ToString() -split '\s+')[0]
  if ($s -match 'emulator|127\.0\.0\.1|25102RKBEC') { continue }
  Write-Output "=== probe $s ==="
  & $adb -s $s shell getprop ro.product.model
  & $adb -s $s shell getprop ro.product.manufacturer
  & $adb -s $s shell getprop ro.product.device
  & $adb -s $s shell wm size
  & $adb -s $s shell getprop ro.build.version.release
}
