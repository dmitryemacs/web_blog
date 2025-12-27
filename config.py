import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class Config:
    # SECRET_KEY обязательно должен быть установлен через переменную окружения в продакшене
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Используем переменную окружения из Docker Compose или .env
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://blog_user:blog_password@localhost:5432/blogdb'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads')

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
