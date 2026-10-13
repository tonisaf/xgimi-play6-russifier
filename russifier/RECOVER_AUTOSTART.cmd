@echo off
chcp 65001 >nul
setlocal
set "beamDevice=192.168.1.100:5555"
set /p "beamDevice=IP проектора:порт [192.168.1.100:5555]: "
set "beamBackup="
set /p "beamBackup=Полный путь к каталогу runs прерванной установки (без кавычек): "
"%~dp0runtime\python.exe" -I "%~dp0launch.py" recover-autostart
set "beamExit=%errorlevel%"
echo.
pause
exit /b %beamExit%
