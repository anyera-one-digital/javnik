#!/bin/bash

# Скрипт для инициализации Django проекта

echo "🚀 Инициализация Django проекта..."

# Проверка наличия .env файла
if [ ! -f .env ]; then
    echo "📝 Создание .env файла из примера..."
    cp .env.example .env
    echo "⚠️  Пожалуйста, отредактируйте .env файл с вашими настройками!"
fi

# Создание миграций
echo "📦 Создание миграций..."
python manage.py makemigrations

# Применение миграций
echo "🗄️  Применение миграций..."
python manage.py migrate

# Сбор статических файлов
echo "📁 Сбор статических файлов..."
python manage.py collectstatic --noinput

echo "✅ Инициализация завершена!"
echo "💡 Для создания суперпользователя выполните: python manage.py createsuperuser"
