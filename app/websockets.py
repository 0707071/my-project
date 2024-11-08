from flask_socketio import SocketIO, emit, join_room
import json

socketio = SocketIO()

def init_websockets(app):
    socketio.init_app(app)

    @socketio.on('join')
    def on_join(data):
        task_id = data.get('task_id')
        if task_id:
            join_room(f'task_{task_id}')
            print(f"Client joined task_{task_id} room")

def send_task_log(task_id, message, stage=None, progress=None, stage_progress=None):
    """Send task log message via WebSocket"""
    data = {
        'task_id': task_id,
        'message': message,
        'stage': stage,
        'progress': progress,
        'stage_progress': stage_progress
    }
    socketio.emit('task_update', data, room=f'task_{task_id}')
