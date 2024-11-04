from flask_socketio import SocketIO, emit, join_room
from datetime import datetime

# Создаем экземпляр SocketIO с поддержкой message_queue для Celery
socketio = SocketIO(message_queue='redis://localhost:6379/0')

def init_websockets(app):
    """Инициализация WebSocket с приложением Flask"""
    socketio.init_app(app, message_queue='redis://localhost:6379/0')

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected'})

@socketio.on('join_task')
def handle_join_task(data):
    task_id = data.get('task_id')
    if task_id:
        join_room(f'task_{task_id}')
        emit('task_log', {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'message': 'Connected to task logs',
            'stage': None,
            'progress': None
        }, room=f'task_{task_id}')

def send_task_log(task_id, message, stage=None, progress=None):
    """
    Отправка лога задачи через WebSocket
    
    Args:
        task_id: ID задачи
        message: Сообщение для лога
        stage: Текущий этап (search/clean/analyze)
        progress: Прогресс этапа (0-100)
    """
    try:
        socketio.emit('task_log', {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'message': message,
            'stage': stage,
            'progress': progress
        }, room=f'task_{task_id}')
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        print(f"Task {task_id} [{stage}]: {message}")
