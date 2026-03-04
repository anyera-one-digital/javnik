# Bookly Backend API

Backend API для приложения Bookly на Django REST Framework с PostgreSQL.

## Технологии

- **Django 5.0** - веб-фреймворк
- **Django REST Framework** - API фреймворк
- **PostgreSQL** - база данных
- **JWT** - аутентификация через токены
- **Docker** - контейнеризация

## Быстрый старт

### 1. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните необходимые значения:

```bash
cp .env.example .env
```

Отредактируйте `.env` файл с вашими настройками.

### 2. Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f backend

# Остановка сервисов
docker-compose down
```

### 3. Создание суперпользователя

```bash
docker-compose exec backend python manage.py createsuperuser
```

### 4. Доступ к API

- API: http://localhost:8000/api/
- Admin панель: http://localhost:8000/admin/

## API Endpoints

### Аутентификация

#### Регистрация
```http
POST /api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "securepassword123",
  "password_confirm": "securepassword123",
  "first_name": "Имя",
  "last_name": "Фамилия",
  "phone": "+79991234567"
}
```

**Ответ:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "first_name": "Имя",
    "last_name": "Фамилия",
    "phone": "+79991234567",
    "avatar": null,
    "is_email_verified": false,
    "created_at": "2024-01-18T22:00:00Z"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "message": "Пользователь успешно зарегистрирован."
}
```

#### Авторизация
```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Ответ:** аналогичен ответу регистрации

#### Выход
```http
POST /api/auth/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

#### Профиль пользователя
```http
GET /api/auth/profile/
Authorization: Bearer <access_token>
```

#### Обновление профиля
```http
PUT /api/auth/profile/update/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "Новое имя",
  "last_name": "Новая фамилия",
  "phone": "+79991234567"
}
```

#### Обновление токена
```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}
```

## Разработка без Docker

### Установка зависимостей

```bash
# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### Настройка базы данных

Убедитесь, что PostgreSQL запущен и создана база данных.

### Миграции

```bash
# Создание миграций
python manage.py makemigrations

# Применение миграций
python manage.py migrate
```

### Запуск сервера разработки

```bash
python manage.py runserver
```

## Структура проекта

```
backend/
├── accounts/              # Приложение для управления пользователями
│   ├── models.py         # Модель User
│   ├── serializers.py    # Сериализаторы для API
│   ├── views.py          # API views
│   └── urls.py           # URL маршруты
├── bookly_api/           # Основные настройки проекта
│   ├── settings.py       # Настройки Django
│   └── urls.py           # Главный URL конфиг
├── manage.py             # Django management script
├── requirements.txt      # Python зависимости
├── Dockerfile            # Docker образ для backend
└── .env.example          # Пример переменных окружения
```

## Переменные окружения

- `DEBUG` - режим отладки (True/False)
- `SECRET_KEY` - секретный ключ Django
- `ALLOWED_HOSTS` - разрешенные хосты
- `POSTGRES_DB` - имя базы данных
- `POSTGRES_USER` - пользователь БД
- `POSTGRES_PASSWORD` - пароль БД
- `POSTGRES_HOST` - хост БД (db для Docker)
- `CORS_ALLOWED_ORIGINS` - разрешенные origins для CORS
- `ACCESS_TOKEN_LIFETIME` - время жизни access токена (минуты)
- `REFRESH_TOKEN_LIFETIME` - время жизни refresh токена (минуты)

## Тестирование API

### Использование curl

```bash
# Регистрация
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123",
    "password_confirm": "testpass123"
  }'

# Авторизация
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'

# Получение профиля
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer <access_token>"
```

## Лендинг (редактирование главной страницы)

В админке раздел **«Лендинг»** разбит на блоки главной страницы:

| Блок | Описание |
|------|----------|
| **Главный экран (Hero)** | Заголовок, описание, SEO |
| **Секции** | «Для кого создан этот сервис», «Вы больше никогда...» — заголовок, описание, картинка, пункты |
| **Блок «Преимущества»** | Заголовок, описание, пункты с иконками |
| **Блок «Истории успеха»** | Заголовок + отзывы (цитата, имя, профессия, фото) |
| **Блок «Тарифы»** | Заголовок, описание, тарифные планы с пунктами |
| **Блок «Вопросы-ответы»** | Заголовок, описание, вопросы и ответы |
| **Блок «Призыв к действию» (CTA)** | Заголовок, кнопки |
| **Изображения лендинга** | Загрузка фото для использования в блоках |

После первой настройки загрузите контент из `content/0.index.yml`:

```bash
docker-compose exec backend python manage.py load_landing_content --force
```

## Полезные команды

```bash
# Создание миграций
docker-compose exec backend python manage.py makemigrations

# Применение миграций
docker-compose exec backend python manage.py migrate

# Создание суперпользователя
docker-compose exec backend python manage.py createsuperuser

# Загрузка контента лендинга
docker-compose exec backend python manage.py load_landing_content

# Сбор статических файлов
docker-compose exec backend python manage.py collectstatic --noinput

# Открытие Django shell
docker-compose exec backend python manage.py shell
```
