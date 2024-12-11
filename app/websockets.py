from flask_socketio import SocketIO, emit, join_room
import json
import logging

socketio = SocketIO()

def init_websockets(app):
    socketio.init_app(app)

    @socketio.on('join')
    def on_join(data):
        task_id = data.get('task_id')
        if task_id:
            room = f'task_{task_id}'
            join_room(room)
            print(f"Client joined room: {room}")

def send_task_log(task_id, message, stage=None, progress=None):
    """Send task log message via WebSocket"""
    try:
        data = {
            'task_id': task_id,
            'message': message,
            'stage': stage,
            'progress': progress
        }
        # Отправляем в конкретную комнату
        room = f'task_{task_id}'
        socketio.emit('task_update', data, room=room, namespace='/')
    except Exception as e:
        logging.error(f"Error sending websocket message: {str(e)}")
