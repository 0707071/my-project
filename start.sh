#!/bin/bash

# Функция для очистки процессов
cleanup() {
    echo "Cleaning up processes..."
    pkill -9 -f celery
    pkill -9 -f "flask run"
    rm -f logs/celery.pid
    rm -f logs/*.pid
    sleep 2  # Даем время на очистку процессов
}

# Проверка наличия необходимых директорий и файлов
check_requirements() {
    # Проверяем наличие директории logs
    if [ ! -d "logs" ]; then
        mkdir -p logs
        echo "Created logs directory"
    fi

    # Проверяем наличие .env файла
    if [ ! -f ".env" ]; then
        echo "ERROR: .env file not found!"
        exit 1
    fi

    # Проверяем наличие OPENAI_API_KEYS в .env
    if ! grep -q "OPENAI_API_KEYS" .env; then
        echo "ERROR: OPENAI_API_KEYS not found in .env"
        exit 1
    fi
}

# Функция для запуска Redis
start_redis() {
    echo "Starting Redis..."
    if ! pgrep redis-server > /dev/null; then
        redis-server &
        sleep 2
        if ! pgrep redis-server > /dev/null; then
            echo "Failed to start Redis"
            exit 1
        fi
    fi
    echo "Redis is running"
}

# Функция для запуска Flask
start_flask() {
    echo "Starting Flask..."
    export FLASK_APP=run.py
    export FLASK_ENV=development
    flask run --host=0.0.0.0 --port=5000 &
    sleep 2
    if ! pgrep -f "flask run" > /dev/null; then
        echo "Failed to start Flask"
        exit 1
    fi
    echo "Flask started successfully"
}

# Функция для запуска Celery
start_celery() {
    echo "Starting Celery..."
    celery -A celery_worker.celery worker \
        --loglevel=INFO \
        --logfile=logs/celery.log \
        --pidfile=logs/celery.pid \
        --concurrency=1 \
        --max-tasks-per-child=1 &

    # Ждем запуска
    for i in {1..10}; do
        if pgrep -f celery > /dev/null; then
            echo "Celery started successfully"
            return 0
        fi
        echo "Waiting for Celery to start... ($i/10)"
        sleep 1
    done

    echo "ERROR: Celery failed to start!"
    return 1
}

# Вызываем cleanup при выходе из скрипта
trap cleanup EXIT

# Проверяем требования
check_requirements

# Убиваем все существующие процессы
cleanup

# Проверяем, что все процессы точно убиты
if pgrep -f celery > /dev/null || pgrep -f "flask run" > /dev/null; then
    echo "Failed to kill all processes"
    exit 1
fi

# Запускаем все компоненты
start_redis
start_flask
start_celery

# Ждем завершения всех процессов
wait

echo "All services started successfully"