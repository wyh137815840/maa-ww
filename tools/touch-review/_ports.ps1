Write-Output '=== listening ports near adb ==='
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Where-Object { $_.LocalPort -in 5555,16384,16416,7555,21503,5037,7897 } |
  Select-Object LocalAddress,LocalPort,OwningProcess |
  Format-Table -AutoSize

Write-Output '=== recent mumu player log (launch/error) ==='
$log = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\log\server\log\MuMuPlayer\log_0.txt'
if (Test-Path $log) {
  Select-String -Path $log -Pattern 'error|Error|fail|Fail|crash|ADB|16384|resolution|display|鸣潮|kuro|launch' |
    Select-Object -Last 40 |
    ForEach-Object { $_.Line }
}
