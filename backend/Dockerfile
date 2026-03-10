# ===========================================
# Backend Dockerfile (Production)
# ===========================================
FROM python:3.14-slim

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создание пользователя для безопасности
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Обновление pip
RUN pip install --no-cache-dir --upgrade pip

# Копирование requirements.txt (для кэширования слоя)
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Создание директорий для static и media
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appuser /app

# Переключение на пользователя без root-прав
USER appuser

# Экспорт порта
EXPOSE 8000

# Запуск через uvicorn
CMD ["uvicorn", "bookly_api.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
