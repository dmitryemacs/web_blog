#!/usr/bin/env python3
# create_tables.py
import os
import sys

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from flask_migrate import Migrate
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Создание таблиц в базе данных"""
    try:
        # Создаем приложение
        app = create_app()
        
        with app.app_context():
            # Создаем все таблицы
            db.create_all()
            logger.info("Таблицы успешно созданы")
            
            # Если нужно, можно добавить тестовые данные
            # from app.models import User, Blog
            # if not User.query.first():
            #     admin = User(username='admin', email='admin@example.com', 
            #                  password='hashed_password', role='admin')
            #     db.session.add(admin)
            #     db.session.commit()
            #     logger.info("Тестовый пользователь создан")
                
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_tables()
