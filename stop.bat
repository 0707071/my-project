@echo off
echo Stopping all services...

:: Stop all services
taskkill /F /IM redis-server.exe
taskkill /F /IM celery.exe
taskkill /F /IM python.exe

echo All services stopped!
pause 