#!/usr/bin/env python3
# create_tables.py - Использует Flask-Migrate для управления схемой БД
import os
import sys
import time

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from flask_migrate import upgrade, init, migrate as _migrate
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_db(max_retries=30, delay=1):
    """Ждем, пока база данных станет доступной"""
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError
    
    db_url = os.environ.get('DATABASE_URL') or \
        'postgresql://blog_user:blog_password@db:5432/blogdb'
    
    for i in range(max_retries):
        try:
            engine = create_engine(db_url.replace('postgresql://', 'postgresql+psycopg2://'))
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            logger.info("База данных доступна")
            return True
        except OperationalError:
            if i < max_retries - 1:
                logger.info(f"Ожидание базы данных... ({i+1}/{max_retries})")
                time.sleep(delay)
            else:
                logger.error("База данных недоступна после всех попыток")
                return False
    return False

def init_db():
    """Инициализация базы данных с использованием миграций"""
    try:
        app = create_app()
        
        with app.app_context():
            # Ждем доступности БД
            if not wait_for_db():
                sys.exit(1)
            
            migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
            
            # Если папка миграций существует, используем Flask-Migrate
            if os.path.exists(migrations_dir):
                try:
                    logger.info("Применение миграций...")
                    upgrade()
                    logger.info("Миграции применены успешно!")
                except Exception as e:
                    error_msg = str(e).lower()
                    # Если база данных уже актуальна, это нормально
                    if "target database is not up to date" in error_msg or "already" in error_msg:
                        logger.info("База данных уже содержит все миграции или требует ручного вмешательства")
                        logger.info("Попытка создать таблицы напрямую (если их нет)...")
                        try:
                            db.create_all()
                            logger.info("Таблицы проверены/созданы успешно!")
                        except Exception:
                            logger.info("Таблицы уже существуют или созданы через миграции")
                    else:
                        logger.warning(f"Ошибка при применении миграций: {e}")
                        logger.info("Попытка создать таблицы напрямую...")
                        try:
                            db.create_all()
                            logger.info("Таблицы созданы напрямую (db.create_all)")
                        except Exception as create_error:
                            logger.error(f"Ошибка при создании таблиц: {create_error}")
                            logger.info("Таблицы, возможно, уже существуют")
            else:
                # Если миграции не инициализированы, создаем таблицы напрямую
                logger.info("Миграции не инициализированы, создаем таблицы напрямую...")
                try:
                    db.create_all()
                    logger.info("Таблицы созданы успешно!")
                except Exception as e:
                    logger.error(f"Ошибка при создании таблиц: {e}", exc_info=True)
                    sys.exit(1)
                
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    init_db()
