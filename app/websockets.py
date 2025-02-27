from flask_socketio import SocketIO, emit, join_room
import json
import logging

# Инициализируем с явными настройками
socketio = SocketIO(
    async_mode='eventlet',     # Используем eventlet
    cors_allowed_origins="*",  # В продакшене заменить на конкретный домен
    logger=True,              # Включаем логирование
    engineio_logger=True,     # Включаем логирование Engine.IO
    ping_timeout=60,          # Увеличиваем таймаут
    ping_interval=25,         # Интервал пингов
    max_http_buffer_size=1e8, # 100MB max message size
    always_connect=True,      # Важно для reconnect
    transports=['websocket', 'polling']  # WebSocket первый
)

def init_websockets(app):
    """Initialize websocket handlers"""
    socketio.init_app(app, 
                     message_queue='redis://',  # Используем Redis для сообщений
                     channel='socketio')        # Канал для сообщений

    @socketio.on('connect')
    def handle_connect():
        logging.info("Client connected")
        emit('connect_response', {'status': 'connected'})

    @socketio.on('disconnect')
    def handle_disconnect():
        logging.info("Client disconnected")

    @socketio.on('join')
    def on_join(data):
        task_id = data.get('task_id')
        if task_id:
            room = f'task_{task_id}'
            join_room(room)
            logging.info(f"Client joined room: {room}")
            emit('join_response', {'status': 'joined', 'room': room})

def send_task_log(task_id, message, stage=None, progress=None, stage_progress=None):
    """Send task log message via WebSocket"""
    try:
        data = {
            'task_id': task_id,
            'message': message,
            'stage': stage,  # search, clean, analyze
            'progress': progress,  # общий прогресс 0-100
            'stage_progress': stage_progress  # прогресс текущего этапа 0-100
        }
        
        # Отправляем в конкретную комнату
        room = f'task_{task_id}'
        logging.info(f"Emitting task_update to room {room}: {data}")
        socketio.emit('task_update', data, room=room, namespace='/')
        
    except Exception as e:
        logging.error(f"Error sending websocket message: {str(e)}")
        logging.exception(e)
