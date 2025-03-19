import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:password@localhost:5432/karhuno'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # API Keys
   #OPENAI_API_KEYS = os.environ.get('OPENAI_API_KEYS')
    APOLLO_API_KEY = os.environ.get('APOLLO_API_KEY')

    # Azure OpenAI API Configuration
    AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
    AZURE_OPENAI_API_VERSION = os.environ.get("AZURE_OPENAI_API_VERSION")
    
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

class ProductionConfig(Config):
    DEBUG = False
    # Add the SERVER_NAME configuration here for production
    SERVER_NAME = 'social_media.karhuno.info'
