# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config 

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login' 

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config) 

    db.init_app(app) 
    migrate.init_app(app, db) 
    login_manager.init_app(app) 

    # Регистрация кастомных фильтров
    from app.custom_filters import nl2br
    app.jinja_env.filters['nl2br'] = nl2br

    # Импорт и регистрация Blueprint
    from app import routes, models
    app.register_blueprint(routes.bp)

    return app
