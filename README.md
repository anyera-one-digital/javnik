# Bookly — Сервис онлайн-записи для частных специалистов

Единый репозиторий с разделённой структурой backend и frontend.

## Структура проекта

```
javnik/
├── backend/          # Django REST API + Uvicorn (ASGI)
├── frontend/         # Nuxt 4 приложение
├── nginx/            # Nginx конфигурация
├── docker-compose.yml
└── .env.example
```

## Быстрый старт

### Запуск через Docker Compose

```bash
# Копирование переменных окружения
cp .env.example .env

# Запуск всех сервисов
make up-d

# Просмотр логов
make logs

# Остановка
make down
```

Или через docker-compose напрямую:

```bash
docker-compose up -d --build
docker-compose logs -f
docker-compose down
```

### Доступ к приложениям

| Сервис | URL |
|--------|-----|
| Приложение | http://localhost:8765 |
| API | http://localhost:8765/api/ |
| Admin панель | http://localhost:8765/admin |

> Порты проброшены только у Nginx (8765). Остальные сервисы доступны только внутри Docker сети.

## Архитектура

```
                    ┌─────────────┐
                    │  Nginx:8765 │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐
     │  Frontend   │ │  Backend  │ │   Redis   │
     │  (Nuxt:3000)│ │(Uvicorn:8k)│ │  (:6379)  │
     └──────┬──────┘ └─────┬─────┘ └───────────┘
            │              │
            │         ┌────▼────┐
            │         │   DB    │
            │         │(:5432)  │
            │         └─────────┘
            │
     ┌──────▼──────┐
     │   Static/   │
     │   Media     │
     └─────────────┘
```

**Маршрутизация Nginx:**
- `/api/**` → Backend (Uvicorn ASGI)
- `/static/**` → Static files
- `/media/**` → Media files
- `/ws/**` → WebSocket (Backend)
- `/` → Frontend (Nuxt SSR)

## Сервисы

| Сервис | Контейнер | Порт | Описание |
|--------|-----------|------|----------|
| Nginx | javnik_nginx | 8765:80 | Reverse proxy |
| Frontend | javnik_frontend | 3000 (внутр.) | Nuxt SSR приложение |
| Backend | javnik_backend | 8000 (внутр.) | Django + Uvicorn (ASGI, 4 workers) |
| PostgreSQL | javnik_db | 5432 (внутр.) | База данных |
| Redis | javnik_redis | 6379 (внутр.) | Кэш/брокер |
| Migrate | javnik_migrate | — | Миграции БД (одноразовый) |

## Разработка

### Backend

```bash
cd backend

# Установка зависимостей
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Запуск (без Docker)
python manage.py runserver
```

### Frontend

```bash
cd frontend

# Установка зависимостей
pnpm install

# Запуск (без Docker)
pnpm dev
```

## Переменные окружения

Скопируйте `.env.example` в `.env` в корне проекта:

```bash
cp .env.example .env
```

При необходимости отредактируйте значения (секретные ключи, пароли, API-ключи).

### Основные переменные

```env
# Database
POSTGRES_DB=javnik_db
POSTGRES_USER=javnik_user
POSTGRES_PASSWORD=your_password

# Backend
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,nginx

# Frontend
NUXT_PUBLIC_API_BASE_URL=/api
```

## Полезные команды

Все команды доступны через Makefile:

```bash
make help              # Показать все доступные команды
```

### Основные команды

```bash
make up-d              # Запустить все сервисы (background)
make down              # Остановить все сервисы
make logs              # Показать логи всех сервисов
make ps                # Показать статус сервисов
```

### Миграции

```bash
make migrate           # Применить миграции
make makemigrations    # Создать файл миграции
make showmigrations    # Показать статус миграций
```

### Статика и данные

```bash
make collectstatic     # Собрать статику backend
make createsuperuser   # Создать суперпользователя
make load-landing-content  # Загрузить контент лендинга
```

### Тесты

```bash
make test              # Запустить тесты backend
make test-app app=accounts   # Тесты конкретного приложения
```

### Frontend

```bash
make frontend-build    # Собрать frontend
make frontend-lint     # Запустить линтер
make frontend-typecheck  # Проверить типы
```

### Очистка

```bash
make clean             # Очистить временные файлы
make clean-volumes     # Удалить volumes (данные БД, redis)
make clean-all         # Полная очистка
```

## Технологии

- **Frontend**: Nuxt 4, Vue 3, TypeScript, Tailwind CSS, Nuxt UI
- **Backend**: Django 5, Django REST Framework, PostgreSQL, Uvicorn (ASGI)
- **Cache**: Redis
- **Web Server**: Nginx (reverse proxy)
- **Контент**: @nuxt/content (YAML)
- **Контейнеризация**: Docker, Docker Compose

## Production рекомендации

1. **Безопасность**:
   - Установите `DEBUG=False`
   - Смените `SECRET_KEY` на случайную строку
   - Настройте HTTPS в Nginx
   - Используйте secrets management для паролей

2. **Производительность**:
   - Настройте количество workers Uvicorn (`--workers`)
   - Включите кэширование в Django через Redis
   - Настройте gzip/brotli в Nginx

3. **Мониторинг**:
   - Логи: `/var/log/nginx/`, Docker logs
