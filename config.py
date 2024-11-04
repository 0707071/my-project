import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # Database
    SQLALCHEMY_DATABASE_URI = 'postgresql://flask:Dr0w$$appostgres@localhost:5432/karhuno'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery configuration
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

class DevelopmentConfig(Config):
    DEVELOPMENT = True

class ProductionConfig(Config):
    DEBUG = False
