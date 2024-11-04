#!/bin/bash

# Проверяем, установлен ли Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 не установлен. Установите Python3 для продолжения."
    exit 1
fi

# Проверяем, установлен ли Redis
if ! command -v redis-cli &> /dev/null; then
    echo "Redis не установлен. Установите Redis для продолжения."
    exit 1
fi

# Создаем виртуальное окружение, если его нет
if [ ! -d "venv" ]; then
    echo "Создаем виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем зависимости
echo "Устанавливаем зависимости..."
pip install -r requirements.txt

# Проверяем статус Redis
redis-cli ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Запускаем Redis..."
    sudo service redis-server start
fi

# Запускаем Celery в фоновом режиме
echo "Запускаем Celery..."
celery -A celery_worker.celery worker --loglevel=info > logs/celery.log 2>&1 &
CELERY_PID=$!

# Запускаем Flask
echo "Запускаем Flask..."
flask run