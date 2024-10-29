from app import create_app, celery

app = create_app()
app.app_context().push()

# Добавим конфигурацию для отключения SSL
celery.conf.update(
    broker_use_ssl=False,
    redis_backend_use_ssl=False,
    broker_connection_retry_on_startup=True
)
