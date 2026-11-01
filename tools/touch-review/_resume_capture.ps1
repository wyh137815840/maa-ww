$adb = 'D:\Program Files\Netease\MuMuPlayer-12.0\nx_main\adb.exe'
# try both old A12 and A15 ports
foreach ($p in @('16384','16416','5555')) {
  & $adb connect "127.0.0.1:$p" 2>&1 | Out-Null
}
& $adb devices -l
Set-Location D:\git\maa-ww
python tools\touch-review\capture.py --label guidebook-or-explore
Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue |
  Select-Object OwningProcess,State | Format-Table -AutoSize
