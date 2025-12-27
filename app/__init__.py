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
    
    # Регистрация обработчиков ошибок
    register_error_handlers(app)

    return app

def register_error_handlers(app):
    """Регистрация централизованных обработчиков ошибок"""
    from flask import render_template
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        # Откатываем транзакцию при ошибке БД
        try:
            db.session.rollback()
        except:
            pass
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return render_template('errors/413.html'), 413
