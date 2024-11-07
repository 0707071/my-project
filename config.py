import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # API Keys
    OPENAI_API_KEYS = os.environ.get('OPENAI_API_KEYS')
    APOLLO_API_KEY = os.environ.get('APOLLO_API_KEY')
    
    # XML Stock
    XMLSTOCK_USER = os.environ.get('XMLSTOCK_USER')
    XMLSTOCK_KEY = os.environ.get('XMLSTOCK_KEY')
    
    # Настройки пула соединений SQLAlchemy
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,  # Увеличиваем размер пула
        'max_overflow': 20,  # Увеличиваем максимальное количество дополнительных соединений
        'pool_timeout': 60,  # Увеличиваем таймаут
        'pool_recycle': 3600,  # Переиспользуем соединения каждый час
        'pool_pre_ping': True  # Проверяем соединения перед использованием
    }

class DevelopmentConfig(Config):
    DEVELOPMENT = True

class ProductionConfig(Config):
    DEBUG = False
