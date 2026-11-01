$ErrorActionPreference = 'Continue'
# Restart mihomo so updated clash-verge.yaml / tun is picked up by Clash Verge service
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -eq 'verge-mihomo.exe' } |
  ForEach-Object {
    Write-Output ("stopping pid=" + $_.ProcessId)
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
  }
Start-Sleep -Seconds 2
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -match 'verge-mihomo|clash-verge' } |
  Select-Object Name, ProcessId |
  Format-Table -AutoSize

# Verify rules present
$cfg = Get-Content 'C:\Users\Administrator\AppData\Roaming\io.github.clash-verge-rev.clash-verge-rev\clash-verge.yaml' -Raw
if ($cfg -match 'MuMuVMMHeadless') { Write-Output 'rules_in_runtime_yaml=yes' } else { Write-Output 'rules_in_runtime_yaml=no' }
if ($cfg -match 'tun:\s*\r?\n\s*enable:\s*true') { Write-Output 'tun_in_runtime_yaml=yes' } else { Write-Output 'tun_in_runtime_yaml=check' }

$vc = Get-Content 'C:\Users\Administrator\AppData\Roaming\io.github.clash-verge-rev.clash-verge-rev\verge.yaml' -Raw
if ($vc -match 'enable_tun_mode:\s*true') { Write-Output 'tun_in_verge_yaml=yes' } else { Write-Output 'tun_in_verge_yaml=no' }
