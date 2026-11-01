$adb = 'D:\leidian\LDPlayer14\adb.exe'
$ip = '192.168.1.3'

Write-Output "=== parallel scan $ip :30000-49999 ==="
$open = [System.Collections.Concurrent.ConcurrentBag[int]]::new()
$ports = 30000..49999
$ports | ForEach-Object -Parallel {
  $ip = $using:ip
  $p = $_
  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $iar = $client.BeginConnect($ip, $p, $null, $null)
    $ok = $iar.AsyncWaitHandle.WaitOne(120, $false)
    if ($ok) {
      try {
        $client.EndConnect($iar) | Out-Null
        ($using:open).Add($p)
      } catch {}
    }
    $client.Close()
  } catch {}
} -ThrottleLimit 100

$found = @($open) | Sort-Object
Write-Output ("open_ports=" + ($found -join ', '))

Write-Output '=== adb connect ==='
foreach ($p in $found) {
  $t = "${ip}:${p}"
  $r = (& $adb connect $t 2>&1 | Out-String).Trim()
  Write-Output "$t => $r"
}

# also try .5 offline entry
(& $adb connect '192.168.1.5:37215' 2>&1 | Out-String).Trim() | Write-Output

Write-Output '=== devices ==='
& $adb devices -l

$devs = (& $adb devices) | Select-String "`tdevice$"
foreach ($d in $devs) {
  $s = ($d.ToString() -split '\s+')[0]
  Write-Output "=== probe $s ==="
  & $adb -s $s shell getprop ro.product.model
  & $adb -s $s shell getprop ro.product.manufacturer
  & $adb -s $s shell getprop ro.product.brand
  & $adb -s $s shell wm size
  & $adb -s $s shell getprop ro.build.version.release
  & $adb -s $s shell pidof com.kurogame.mingchao
}
