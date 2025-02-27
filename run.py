import eventlet
eventlet.monkey_patch(socket=True, select=True)

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app, 
                debug=True, 
                host='0.0.0.0', 
                port=5000,
                use_reloader=False,  # Важно для eventlet
                log_output=True)
