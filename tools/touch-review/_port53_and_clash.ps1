Write-Host '=== listeners :53 / :7897 ==='
Get-NetUDPEndpoint -LocalPort 53 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,OwningProcess |
  ForEach-Object {
    $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
    "{0}:{1} pid={2} name={3}" -f $_.LocalAddress, $_.LocalPort, $_.OwningProcess, $p.ProcessName
  }
Get-NetTCPConnection -LocalPort 53,7897,9097,33331 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress,LocalPort,State,OwningProcess -Unique |
  ForEach-Object {
    $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
    "tcp {0}:{1} {2} pid={3} {4}" -f $_.LocalAddress, $_.LocalPort, $_.State, $_.OwningProcess, $p.ProcessName
  }

Write-Host '=== verge flags now ==='
Select-String -Path "$env:APPDATA\io.github.clash-verge-rev.clash-verge-rev\verge.yaml" -Pattern 'enable_system_proxy|enable_dns_settings|enable_tun_mode'

Write-Host '=== flushdns ==='
ipconfig /flushdns | Out-Host

Write-Host '=== Resolve via 223.5.5.5 ==='
nslookup www.baidu.com 223.5.5.5
nslookup gface.kurogame.com 223.5.5.5
