from flask import Blueprint

# Создаем blueprint без url_prefix
bp = Blueprint('auth', __name__)

# Импортируем routes после создания bp
from app.auth import routes
