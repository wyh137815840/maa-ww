Write-Output '=== net adapters ==='
Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, MacAddress | Format-Table -AutoSize -Wrap

Write-Output '=== ipv4 ==='
Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike '127.*' } |
  Select-Object InterfaceAlias, IPAddress, PrefixLength |
  Format-Table -AutoSize

Write-Output '=== arp recent ==='
arp -a | Select-Object -First 40

# Try common MuMu bridge adb
$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
$candidates = @('127.0.0.1:16384','127.0.0.1:7555','127.0.0.1:5555')
# scan local /24 of 以太网 for :5555 is heavy; try connect localhost ports first
foreach ($c in $candidates) {
  Write-Output ("try " + $c)
  & $adb connect $c 2>&1 | Out-String | Write-Output
}
& $adb devices
