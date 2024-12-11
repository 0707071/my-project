@echo off
echo Starting development environment...

:: Start Redis
echo Starting Redis...
start /B redis-server

:: Start Celery worker
echo Starting Celery...
start /B celery -A app.celery worker --loglevel=info --pool=solo

:: Start Flask development server
echo Starting Flask...
start /B flask run --debug

echo All services started! Press any key to stop all services...
pause

:: Cleanup
taskkill /F /IM redis-server.exe
taskkill /F /IM celery.exe
taskkill /F /IM python.exe 