#!/bin/bash
# init-db.sh

# Ждем, пока база данных будет готова
echo "Ожидание подключения к базе данных..."
while ! nc -z db 5432; do
  sleep 1
done
echo "База данных готова!"

# Инициализируем миграции, если папка не существует
if [ ! -d "migrations" ]; then
    echo "Инициализация папки миграций..."
    flask db init
fi

# Создаем миграцию
echo "Создание миграций..."
flask db migrate -m "Initial tables"

# Применяем миграцию
echo "Применение миграций..."
flask db upgrade

echo "База данных инициализирована успешно!"
