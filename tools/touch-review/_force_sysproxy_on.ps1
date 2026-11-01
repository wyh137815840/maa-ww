$verge = Join-Path $env:APPDATA 'io.github.clash-verge-rev.clash-verge-rev\verge.yaml'
$txt = [IO.File]::ReadAllText($verge)
$txt2 = [regex]::Replace($txt, '(?m)^enable_system_proxy:\s*\w+\s*$', 'enable_system_proxy: true')
[IO.File]::WriteAllText($verge, $txt2)
Select-String -Path $verge -Pattern 'enable_system_proxy|enable_dns|enable_tun'
$reg = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
Set-ItemProperty $reg -Name ProxyEnable -Value 1
Set-ItemProperty $reg -Name ProxyServer -Value '127.0.0.1:7897'
'ProxyEnable=' + (Get-ItemProperty $reg).ProxyEnable + ' ProxyServer=' + (Get-ItemProperty $reg).ProxyServer
try { 'baidu=' + (Invoke-WebRequest https://www.baidu.com -UseBasicParsing -TimeoutSec 5).StatusCode } catch { "baidu fail: $_" }
Get-Process clash-verge,verge-mihomo -ErrorAction SilentlyContinue | Format-Table Name,Id -AutoSize
