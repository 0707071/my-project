from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from celery import Celery
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

# Инициализируем расширения
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
celery = Celery('app', 
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0',
                broker_connection_retry_on_startup=True)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Настройка логирования
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/karhuno.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Karhuno startup')

    # Инициализируем расширения
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Настраиваем login_manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Регистрируем blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.logger.info('Registered auth blueprint')
    app.logger.info(f'Auth routes: {[rule.rule for rule in app.url_map.iter_rules() if rule.endpoint.startswith("auth")]}')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    app.logger.info('Registered main blueprint')
    app.logger.info(f'Main routes: {[rule.rule for rule in app.url_map.iter_rules() if rule.endpoint.startswith("main")]}')

    return app

# Импортируем модели здесь, чтобы избежать циклических импортов
from app.models import user, client, prompt, search_query, search_result, task
