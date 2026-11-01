Get-CimInstance Win32_Process |
  Where-Object { $_.Name -match 'clash|verge|mihomo|Clash' } |
  Select-Object Name, ProcessId, ExecutablePath |
  Format-Table -AutoSize -Wrap

$ie = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
"ProxyEnable=$($ie.ProxyEnable) ProxyServer=$($ie.ProxyServer)"
