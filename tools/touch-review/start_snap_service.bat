@echo off
title MaaWW Snap Service (Ctrl+Alt+Space)
cd /d D:\git\maa-ww
set "PY=python"
where py >nul 2>&1 && set "PY=py -3"
echo Starting snap service...
%PY% tools\touch-review\snap_service.py
echo.
echo Service exited. Press any key to close.
pause >nul
