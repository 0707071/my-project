from flask_socketio import SocketIO, emit, join_room
from app import create_app
from datetime import datetime

socketio = SocketIO()

def init_websockets(app):
    socketio.init_app(app)

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
            'message': 'Подключено к логам задачи'
        }, room=f'task_{task_id}')

def send_task_log(task_id, message):
    """
    Отправка лога задачи через WebSocket
    """
    socketio.emit('task_log', {
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'message': message
    }, room=f'task_{task_id}')
