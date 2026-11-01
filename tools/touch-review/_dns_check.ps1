Write-Host '=== DNS via 8.8.8.8 ==='
nslookup api.kurogame.com 8.8.8.8
Write-Host '=== DNS via 192.168.1.1 ==='
nslookup api.kurogame.com 192.168.1.1
Write-Host '=== DNS via 144.144.144.144 ==='
nslookup api.kurogame.com 144.144.144.144
Write-Host '=== ProxyEnable ==='
(Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings').ProxyEnable
Write-Host '=== Processes ==='
Get-CimInstance Win32_Process | Where-Object {
  $_.Name -match 'MuMu|Clash|verge|Client-Win64|launcher|Wuthering|aki|Shell'
} | Select-Object Name, ProcessId | Format-Table -AutoSize
