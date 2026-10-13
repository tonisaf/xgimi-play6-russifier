@echo off
chcp 65001 >nul
setlocal
set "beamDevice=192.168.1.100:5555"
set /p "beamDevice=IP проектора:порт [192.168.1.100:5555]: "
"%~dp0runtime\python.exe" -I "%~dp0launch.py" update-boot --bundle "%~dp0boot-helper"
set "beamExit=%errorlevel%"
echo.
pause
exit /b %beamExit%
