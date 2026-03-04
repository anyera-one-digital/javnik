FROM python:3.11-slim

WORKDIR /app

# Установка только необходимых зависимостей (упрощено для разработки)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Обновление pip
RUN pip install --no-cache-dir --upgrade pip

# Копирование requirements.txt (для кэширования слоя)
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Создание директорий
RUN mkdir -p /app/staticfiles /app/media

# Команда по умолчанию
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
