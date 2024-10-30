#!/bin/bash

# Проверяем, активировано ли виртуальное окружение
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Активируем виртуальное окружение..."
    source venv/bin/activate
fi

# Функция для остановки всех процессов при выходе
cleanup() {
    echo "Останавливаем все процессы..."
    kill $(jobs -p)
    exit
}

# Регистрируем функцию очистки
trap cleanup EXIT

# Проверяем и запускаем Redis, если не запущен
if ! pgrep redis-server > /dev/null; then
    echo "Запускаем Redis..."
    redis-server &
    sleep 2
fi

# Запускаем Celery worker
echo "Запускаем Celery worker..."
celery -A celery_worker.celery worker --loglevel=info &

# Ждем запуска Celery
sleep 2

# Запускаем Flask приложение
echo "Запускаем Flask приложение..."
flask run --debug &

# Выводим информацию о запущенных процессах
echo -e "\nПриложение запущено!"
echo "* Flask: http://127.0.0.1:5000"
echo "* Redis: localhost:6379"
echo "* Celery worker активен"
echo -e "\nДля остановки нажмите Ctrl+C\n"

# Ждем завершения всех процессов
wait 