from app import create_app, db
import os

app = create_app()

# Создаем папку для загрузок при запуске
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
