FROM python:3.9-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование остальных файлов проекта
COPY . .

# Создание папок
RUN mkdir -p /app/static/uploads
RUN chmod -R 755 /app/static/uploads

# Настройка переменных окружения
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Делаем скрипты исполняемыми
RUN chmod +x init-db.sh

# Открытие порта
EXPOSE 5000

# Запуск приложения
CMD ["flask", "run", "--host=0.0.0.0"]
