from app import create_app, celery

app = create_app()
app.app_context().push()

# Добавим конфигурацию для WebSocket
celery.conf.update(
    broker_use_ssl=False,
    redis_backend_use_ssl=False,
    broker_connection_retry_on_startup=True,
    task_routes={
        'app.tasks.*': {'queue': 'default'}
    },
    broker_transport_options={'visibility_timeout': 3600},
    result_backend_transport_options={'visibility_timeout': 3600}
)
