Get-CimInstance Win32_Process |
  Where-Object { $_.Name -match 'clash|verge|mihomo|mumu|MuMu|Nemu|nx_main|MuMuNx' } |
  Select-Object Name, ProcessId, ExecutablePath |
  Format-Table -AutoSize

$ie = Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
"ProxyEnable=$($ie.ProxyEnable)"
"ProxyServer=$($ie.ProxyServer)"
"ProxyOverride=$($ie.ProxyOverride)"
