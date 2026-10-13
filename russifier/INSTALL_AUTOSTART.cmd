@echo off
chcp 65001 >nul
setlocal
echo Экспериментальная первая установка с автозапуском. На другом проекторе пока не проверена.
set "beamDevice=192.168.1.100:5555"
set /p "beamDevice=IP проектора:порт [192.168.1.100:5555]: "
"%~dp0runtime\python.exe" -I "%~dp0launch.py" install-autostart
set "beamExit=%errorlevel%"
echo.
pause
exit /b %beamExit%
