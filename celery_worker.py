from app import create_app, celery
import logging
from logging.handlers import RotatingFileHandler

# Настраиваем логирование
logger = logging.getLogger('celery')
handler = RotatingFileHandler('logs/celery.log', maxBytes=10240, backupCount=10)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s'
))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = create_app()
app.app_context().push()

# Добавим тестовое сообщение при старте
logger.info("Celery worker started")

# Добавим конфигурацию для Celery
celery.conf.update(
    broker_use_ssl=False,
    redis_backend_use_ssl=False,
    broker_connection_retry_on_startup=True,
    task_routes={
        'app.tasks.*': {'queue': 'default'}
    },
    broker_transport_options={'visibility_timeout': 3600},
    result_backend_transport_options={'visibility_timeout': 3600},
    worker_prefetch_multiplier=1,  # Важно для предотвращения перегрузки
    worker_max_tasks_per_child=1   # Перезапуск воркера после каждой задачи
)
