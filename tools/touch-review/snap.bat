@echo off
setlocal
REM Quick ADB snap into review/inbox (1280x720, mumuscreen001).

cd /d D:\git\maa-ww
set "PY=python"
where py >nul 2>&1 && set "PY=py -3"

echo [%TIME%] capturing...
%PY% tools\touch-review\capture.py --label snap
if errorlevel 1 (
  echo CAPTURE FAILED
  powershell -NoProfile -Command "[console]::Beep(400,250)" 2>nul
  ping -n 3 127.0.0.1 >nul
  exit /b 1
)
powershell -NoProfile -Command "[console]::Beep(880,120)" 2>nul
echo OK. Saved to review\inbox\*-snap.png
ping -n 2 127.0.0.1 >nul
exit /b 0
