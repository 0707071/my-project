from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from celery import Celery
from config import Config

# Инициализируем расширения
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
celery = Celery('app', broker=Config.CELERY_BROKER_URL)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализируем расширения с приложением
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Настраиваем Celery
    celery.conf.update(app.config)

    # Импортируем и инициализируем WebSocket
    from app.websockets import init_websockets
    init_websockets(app)

    # Регистрируем blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app

# Импортируем модели здесь, чтобы избежать циклических импортов
from app.models import user, client, prompt, search_query, search_result, task
