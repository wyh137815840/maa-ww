$ErrorActionPreference = 'Continue'

function Find-Adb {
  $cands = @(
    'C:\leidian\LDPlayer9\adb.exe',
    'D:\leidian\LDPlayer9\adb.exe',
    'C:\LDPlayer\LDPlayer9\adb.exe',
    'C:\Program Files\ldplayer9box\adb.exe',
    # LDPlayer / 雷电 14 common layouts
    'C:\leidian\LDPlayer14\adb.exe',
    'D:\leidian\LDPlayer14\adb.exe',
    'C:\LDPlayer\LDPlayer14\adb.exe',
    'D:\LDPlayer\LDPlayer14\adb.exe',
    'C:\Program Files\ldplayer14box\adb.exe',
    'C:\Program Files\LDPlayer\LDPlayer14\adb.exe',
    'D:\Program Files\LDPlayer\LDPlayer14\adb.exe',
    'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
  )
  foreach ($c in $cands) { if (Test-Path $c) { return $c } }

  # deep-ish search under known roots
  foreach ($root in @('C:\leidian','D:\leidian','C:\LDPlayer','D:\LDPlayer','C:\Program Files','D:\Program Files')) {
    if (-not (Test-Path $root)) { continue }
    $hit = Get-ChildItem $root -Recurse -Filter adb.exe -ErrorAction SilentlyContinue |
      Where-Object { $_.FullName -match 'LDPlayer|leidian|ldplayer' } |
      Select-Object -First 3
    foreach ($h in $hit) { return $h.FullName }
  }
  $w = Get-Command adb -ErrorAction SilentlyContinue
  if ($w) { return $w.Source }
  return $null
}

Write-Output '=== processes ==='
Get-Process -ErrorAction SilentlyContinue |
  Where-Object { $_.ProcessName -match 'ld|leidian|dnplayer|LdVBox|Ld9|Ld14|dnplayer' } |
  ForEach-Object { Write-Output ("{0} pid={1} path={2}" -f $_.ProcessName, $_.Id, $_.Path) }

Write-Output '=== folders ==='
foreach ($root in @('C:\Program Files','D:\Program Files','C:\','D:\')) {
  if (-not (Test-Path $root)) { continue }
  Get-ChildItem $root -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match 'ld|leidian|雷电|雷神|LDPlayer' } |
    ForEach-Object { Write-Output $_.FullName }
}

$adb = Find-Adb
if (-not $adb) { Write-Output 'NO_ADB'; exit 1 }
Write-Output "adb=$adb"

& $adb kill-server 2>$null | Out-Null
Start-Sleep -Milliseconds 300
& $adb start-server | Out-Null

# Classic + LD14-ish local ports; also harvest listening ports in adb ranges
$ports = [System.Collections.Generic.HashSet[int]]::new()
foreach ($p in 5554,5555,5556,5557,5558,5559,62001,7555,16384,16416,16448,16480,16512) { [void]$ports.Add($p) }
try {
  Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object {
      ($_.LocalAddress -eq '127.0.0.1' -or $_.LocalAddress -eq '0.0.0.0' -or $_.LocalAddress -eq '::' -or $_.LocalAddress -eq '::1') -and
      (
        ($_.LocalPort -ge 5550 -and $_.LocalPort -le 5600) -or
        ($_.LocalPort -ge 16384 -and $_.LocalPort -le 16600) -or
        $_.LocalPort -in 62001,7555,21503
      )
    } |
    ForEach-Object { [void]$ports.Add([int]$_.LocalPort) }
} catch {}

Write-Output '=== candidate ports ==='
$ports | Sort-Object | ForEach-Object { Write-Output $_ }

Write-Output '=== connect (3s timeout) ==='
foreach ($p in ($ports | Sort-Object)) {
  $c = "127.0.0.1:$p"
  $job = Start-Job -ScriptBlock {
    param($adbPath, $target)
    & $adbPath connect $target 2>&1 | Out-String
  } -ArgumentList $adb, $c
  if (Wait-Job $job -Timeout 3) {
    $r = (Receive-Job $job | Out-String).Trim()
    Remove-Job $job -Force
    if ($r -match 'connected|already') { Write-Output "HIT $c :: $r" }
    else { Write-Output "miss $c :: $r" }
  } else {
    Stop-Job $job -Force
    Remove-Job $job -Force
    Write-Output "timeout $c"
  }
}

Write-Output '=== devices ==='
& $adb devices -l

$devs = (& $adb devices) | Select-String "`tdevice$"
foreach ($d in $devs) {
  $s = ($d.ToString() -split '\s+')[0]
  Write-Output "=== probe $s ==="
  & $adb -s $s shell getprop ro.product.model
  & $adb -s $s shell getprop ro.build.version.release
  & $adb -s $s shell wm size
  & $adb -s $s shell getprop ro.product.manufacturer
  $pkg = & $adb -s $s shell pm path com.kurogame.mingchao 2>$null
  Write-Output ("mingchao=$pkg")
  & $adb -s $s shell pidof com.kurogame.mingchao
}
