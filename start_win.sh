# #!/bin/bash

#  # For cleaning up processes (replace pkill with taskkill):
# cleanup() {
#     echo "Cleaning up processes..."
#     taskkill /F /IM "celery.exe"
#     taskkill /F /IM "flask.exe"
#     rm -f logs/celery.pid
#     rm -f logs/*.pid
#     sleep 2  # Give time to clean up processes
# }


# # For checking if Redis is running (replace pgrep with tasklist):
# start_redis() {
#     echo "Starting Redis..."
#     if ! tasklist /FI "IMAGENAME eq redis-server.exe" | findstr "redis-server.exe" >nul; then
#         # Start Redis in Docker
#         docker run -d --name redis -p 6379:6379 redis
#         sleep 2
#         if ! tasklist /FI "IMAGENAME eq redis-server.exe" | findstr "redis-server.exe" >nul; then
#             echo "Failed to start Redis"
#             exit 1
#         fi
#     fi
#     echo "Redis is running"
# }
# # Функция для очистки процессов
# # cleanup() {
# #     echo "Cleaning up processes..."
# #     pkill -9 -f celery
# #     pkill -9 -f "flask run"
# #     rm -f logs/celery.pid
# #     rm -f logs/*.pid
# #     sleep 2  # Даем время на очистку процессов
# # }

# # Проверка наличия необходимых директорий и файлов
# check_requirements() {
#     # Проверяем наличие директории logs
#     if [ ! -d "logs" ]; then
#         mkdir -p logs
#         echo "Created logs directory"
#     fi

#     # Проверяем наличие .env файла
#     if [ ! -f ".env" ]; then
#         echo "ERROR: .env file not found!"
#         exit 1
#     fi

#     # Проверяем наличие OPENAI_API_KEYS в .env
#     if ! grep -q "OPENAI_API_KEYS" .env; then
#         echo "ERROR: OPENAI_API_KEYS not found in .env"
#         exit 1
#     fi
# }

# # Функция для запуска Redis
# # start_redis() {
# #     echo "Starting Redis..."
# #     if ! pgrep redis-server > /dev/null; then
# #         redis-server &
# #         sleep 2
# #         if ! pgrep redis-server > /dev/null; then
# #             echo "Failed to start Redis"
# #             exit 1
# #         fi
# #     fi
# #     echo "Redis is running"
# # }

# # Функция для запуска Flask
# start_flask() {
#     echo "Starting Flask..."
#     export FLASK_APP=run.py
#     export FLASK_ENV=development
#     flask run --host=0.0.0.0 --port=5000 &
#     sleep 2
#     if ! pgrep -f "flask run" > /dev/null; then
#         echo "Failed to start Flask"
#         exit 1
#     fi
#     echo "Flask started successfully"
# }

# # Функция для запуска Celery
# start_celery() {
#     echo "Starting Celery..."
#     celery -A celery_worker.celery worker \
#         --loglevel=INFO \
#         --logfile=logs/celery.log \
#         --pidfile=logs/celery.pid \
#         --concurrency=1 \
#         --max-tasks-per-child=1 &

#     # Ждем запуска
#     for i in {1..10}; do
#         if pgrep -f celery > /dev/null; then
#             echo "Celery started successfully"
#             return 0
#         fi
#         echo "Waiting for Celery to start... ($i/10)"
#         sleep 1
#     done

#     echo "ERROR: Celery failed to start!"
#     return 1
# }

# # Вызываем cleanup при выходе из скрипта
# trap cleanup EXIT

# # Проверяем требования
# check_requirements

# # Убиваем все существующие процессы
# cleanup

# # # Проверяем, что все процессы точно убиты
# # if pgrep -f celery > /dev/null || pgrep -f "flask run" > /dev/null; then
# #     echo "Failed to kill all processes"
# #     exit 1
# # fi

# # Check if Celery or Flask processes are still running (Windows-compatible)
# if tasklist /FI "IMAGENAME eq celery.exe" | findstr "celery.exe" >nul || tasklist /FI "IMAGENAME eq flask.exe" | findstr "flask.exe" >nul; then
#     echo "Failed to kill all processes"
#     exit 1
# fi

# # Запускаем все компоненты
# start_redis
# start_flask
# start_celery

# # Ждем завершения всех процессов
# wait

# echo "All services started successfully"

#-------------------------------------------------------------------------------

#!/bin/bash

# # For cleaning up processes (replace pkill with taskkill):
# cleanup() {
#     echo "Cleaning up processes..."
#     taskkill /F /IM "celery.exe" >nul 2>&1
#     taskkill /F /IM "flask.exe" >nul 2>&1
#     rm -f logs/celery.pid
#     rm -f logs/*.pid
#     sleep 2  # Give time to clean up processes
# }

# # For checking if Redis is running (replace pgrep with tasklist):
# start_redis() {
#     echo "Starting Redis..."
#     if ! tasklist /FI "IMAGENAME eq redis-server.exe" | findstr "redis-server.exe" >nul; then
#         # Start Redis in Docker
#         docker run -d --name redis -p 6379:6379 redis
#         sleep 2
#         if ! tasklist /FI "IMAGENAME eq redis-server.exe" | findstr "redis-server.exe" >nul; then
#             echo "Failed to start Redis"
#             exit 1
#         fi
#     fi
#     echo "Redis is running"
# }

# # Checking requirements for logs directory and .env file:

# # Function to check if OPENAI_API_KEYS exists in .env file
# check_requirements() {
#     # Check if logs directory exists
#     if [ ! -d "logs" ]; then
#         mkdir -p logs
#         echo "Created logs directory"
#     fi

#     # Check if .env file exists
#     if [ ! -f ".env" ]; then
#         echo "ERROR: .env file not found!"
#         exit 1
#     fi

#     # Check if OPENAI_API_KEYS exists in .env using findstr for Windows compatibility
#     if ! findstr "OPENAI_API_KEYS" .env >nul; then
#         echo "ERROR: OPENAI_API_KEYS not found in .env"
#         exit 1
#     fi
# }



# # Function to start Flask
# # Function to start Flask
# start_flask() {
#     echo "Starting Flask..."
#     export FLASK_APP=run.py
#     export FLASK_ENV=development
#     flask run --host=0.0.0.0 --port=5000 &
#     sleep 2
    
#     # Check if Flask is running using tasklist (Windows-compatible)
#     if tasklist /FI "IMAGENAME eq flask.exe" | findstr "flask.exe" >nul; then
#         echo "Flask started successfully"
#     else
#         echo "Failed to start Flask"
#         exit 1
#     fi
# }

# # Function to start Celery
# start_celery() {
#     echo "Starting Celery..."
#     celery -A celery_worker.celery worker \
#         --loglevel=INFO \
#         --logfile=logs/celery.log \
#         --pidfile=logs/celery.pid \
#         --concurrency=1 \
#         --max-tasks-per-child=1 &

#     # Wait for Celery to start
#     # Function to start Celery
# start_celery() {
#     echo "Starting Celery..."
#     celery -A celery_worker.celery worker \
#         --loglevel=INFO \
#         --logfile=logs/celery.log \
#         --pidfile=logs/celery.pid \
#         --concurrency=1 \
#         --max-tasks-per-child=1 &

#     # Wait for Celery to start (Windows-compatible)
#     for i in {1..10}; do
#         # Use tasklist and findstr to check if Celery is running
#         if tasklist /FI "IMAGENAME eq celery.exe" | findstr "celery.exe" >nul; then
#             echo "Celery started successfully"
#             return 0
#         fi
#         echo "Waiting for Celery to start... ($i/10)"
#         sleep 1
#     done

#     echo "ERROR: Celery failed to start!"
#     return 1
# }





    

# # Trap cleanup on exit
# trap cleanup EXIT

# # Check requirements before proceeding
# check_requirements

# # Kill any existing processes
# cleanup

# # Ensure no Flask or Celery processes are still running
# if tasklist /FI "IMAGENAME eq celery.exe" | findstr "celery.exe" >nul || tasklist /FI "IMAGENAME eq flask.exe" | findstr "flask.exe" >nul; then
#     echo "Failed to kill all processes"
#     exit 1
# fi

# # Start Redis, Flask, and Celery
# start_redis
# start_flask
# start_celery

# # Wait for processes to complete
# wait

# echo "All services started successfully"

#---------------------------------------------
# Function to clean up processes (replace pkill with taskkill)
cleanup() {
    echo "Cleaning up processes..."
<<<<<<< HEAD
    taskkill /F /IM "celery.exe" >nul 2>&1
    taskkill /F /IM "flask.exe" >nul 2>&1
    taskkill /F /IM "redis-server.exe" >nul 2>&1
    docker rm -f redis >nul 2>&1   # Stop Redis container if running
=======
    pkill -9 -f celery
    pkill -9 -f "python run.py"  # Изменено для нового процесса
>>>>>>> 62caa4524096a8dd513ac4aa0ac6ba17e8c3b192
    rm -f logs/celery.pid
    rm -f logs/*.pid
    sleep 2  # Give time to clean up processes
}

# Function to check if Redis is running (replace pgrep with tasklist)
start_redis() {
    echo "Starting Redis..."
    # Check if Redis is already running
    if ! tasklist /FI "IMAGENAME eq redis-server.exe" | findstr "redis-server.exe" >nul; then
        # Start Redis in Docker if not running
        docker run -d --name redis -p 6379:6379 redis
        sleep 2
        # Verify Redis started
        if ! tasklist /FI "IMAGENAME eq redis-server.exe" | findstr "redis-server.exe" >nul; then
            echo "Failed to start Redis"
            exit 1
        fi
    fi
    echo "Redis is running"
}

<<<<<<< HEAD
# Function to check for necessary requirements (.env and logs directory)
check_requirements() {
    # Check if logs directory exists, create if it doesn't
    if [ ! -d "logs" ]; then
        mkdir -p logs
        echo "Created logs directory"
    fi

    # Check if .env file exists
    if [ ! -f ".env" ]; then
        echo "ERROR: .env file not found!"
        exit 1
    fi

    # Check if OPENAI_API_KEYS exists in .env using findstr for Windows compatibility
    if ! findstr "OPENAI_API_KEYS" .env >nul; then
        echo "ERROR: OPENAI_API_KEYS not found in .env"
        exit 1
    fi
}

# Function to start Flask (Windows-compatible)
start_flask() {
    echo "Starting Flask..."
    export FLASK_APP=run.py
    export FLASK_ENV=development
    flask run --host=0.0.0.0 --port=5000 &   # Start Flask in background
    sleep 2
    
    # Check if Flask is running using tasklist (Windows-compatible)
    if tasklist /FI "IMAGENAME eq flask.exe" | findstr "flask.exe" >nul; then
        echo "Flask started successfully"
    else
        echo "Failed to start Flask"
        exit 1
    fi
=======
# Функция для запуска Flask с Socket.IO
start_flask() {
    echo "Starting Flask with Socket.IO..."
    python run.py > logs/flask.log 2>&1 &
    local flask_pid=$!
    echo $flask_pid > logs/flask.pid
    
    # Ждем запуска
    for i in {1..10}; do
        if curl -s http://localhost:5000 > /dev/null; then
            echo "Flask started successfully (PID: $flask_pid)"
            return 0
        fi
        echo "Waiting for Flask to start... ($i/10)"
        sleep 1
    done

    echo "ERROR: Flask failed to start!"
    return 1
>>>>>>> 62caa4524096a8dd513ac4aa0ac6ba17e8c3b192
}

# Function to start Celery (Windows-compatible)
start_celery() {
    echo "Starting Celery..."
    celery -A celery_worker.celery worker \
        --loglevel=INFO \
        --logfile=logs/celery.log \
        --pidfile=logs/celery.pid \
        --concurrency=1 \
        --max-tasks-per-child=1 &

    # Wait for Celery to start (Windows-compatible)
    for i in {1..10}; do
        if tasklist /FI "IMAGENAME eq celery.exe" | findstr "celery.exe" >nul; then
            echo "Celery started successfully"
            return 0
        fi
        echo "Waiting for Celery to start... ($i/10)"
        sleep 1
    done

    echo "ERROR: Celery failed to start!"
    return 1
}

# Trap cleanup on exit
trap cleanup EXIT

# Check requirements before proceeding
check_requirements

# Kill any existing processes
cleanup

<<<<<<< HEAD
# Ensure no Flask or Celery processes are still running
if tasklist /FI "IMAGENAME eq celery.exe" | findstr "celery.exe" >nul || tasklist /FI "IMAGENAME eq flask.exe" | findstr "flask.exe" >nul; then
=======
# Проверяем, что все процессы точно убиты
if pgrep -f celery > /dev/null || pgrep -f "python run.py" > /dev/null; then
>>>>>>> 62caa4524096a8dd513ac4aa0ac6ba17e8c3b192
    echo "Failed to kill all processes"
    exit 1
fi

# Start Redis, Flask, and Celery
start_redis
start_flask
start_celery

# Wait for processes to complete
wait

echo "All services started successfully"
