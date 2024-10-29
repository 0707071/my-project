from app import create_app, celery
from app.websockets import socketio

app = create_app()
app.app_context().push()  # Добавляем это для работы с контекстом приложения

if __name__ == '__main__':
    socketio.run(app, debug=True)
