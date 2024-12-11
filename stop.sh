#!/bin/bash

# Останавливаем Flask (если запущен через start.sh)
if [ -f ".flask.pid" ]; then
    kill $(cat .flask.pid)
    rm .flask.pid
fi

# Останавливаем Celery
pkill -f 'celery worker'

# Деактивируем виртуальное окружение
deactivate

echo "Все процессы остановлены" 