"""
Django settings for bookly_api project.
"""
import os
from pathlib import Path
from decouple import config
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ===========================================
# SECURITY SETTINGS
# ===========================================
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

# Админский код для обхода подтверждения email (только при DEBUG).
EMAIL_VERIFY_ADMIN_CODE = config('EMAIL_VERIFY_ADMIN_CODE', default=None)
if DEBUG and not EMAIL_VERIFY_ADMIN_CODE:
    EMAIL_VERIFY_ADMIN_CODE = '000000'

# ALLOWED_HOSTS
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1'
).split(',')

# В режиме разработки добавляем дополнительные хосты
if DEBUG:
    ALLOWED_HOSTS.extend(['0.0.0.0', 'backend', 'nginx', 'localhost:8765'])
    ALLOWED_HOSTS = list(set(ALLOWED_HOSTS))  # Убираем дубликаты

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost,http://localhost:8765,http://localhost:4000,http://127.0.0.1:8765,http://127.0.0.1:4000'
).split(',')

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    
    # Local apps
    'accounts',
    'bookings',
    'landing',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bookly_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'bookly_api.wsgi.application'

# ASGI_APPLICATION для uvicorn
ASGI_APPLICATION = 'bookly_api.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', default='bookly_db'),
        'USER': config('POSTGRES_USER', default='bookly_user'),
        'PASSWORD': config('POSTGRES_PASSWORD', default='bookly_password'),
        'HOST': config('POSTGRES_HOST', default='db'),
        'PORT': config('POSTGRES_PORT', default='5432'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email settings
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@bookly.com')

# Yandex Maps API (Geosuggest, Geocoder) — для подсказок адресов и отображения на карте
# Получить ключ: https://developer.tech.yandex.com/
YANDEX_MAPS_API_KEY = config('YANDEX_MAPS_API_KEY', default='')

# DaData API — fallback для подсказок адресов (если нет Yandex ключа)
# Бесплатно ~10k запросов/день: https://dadata.ru/
DADATA_API_KEY = config('DADATA_API_KEY', default='')

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('ACCESS_TOKEN_LIFETIME', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=config('REFRESH_TOKEN_LIFETIME', default=1440, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': config('JWT_ALGORITHM', default='HS256'),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS settings
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost,http://localhost:80,http://frontend:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)
CORS_ALLOW_CREDENTIALS = config('CORS_ALLOW_CREDENTIALS', default=True, cast=bool)
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Разрешить все origins в режиме разработки

# Redis settings
REDIS_URL = config('REDIS_URL', default='redis://redis:6379/0')

# Cache settings (опционально, можно использовать Redis)
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': REDIS_URL,
#     }
# }

# ===========================================
# LOGGING
# ===========================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
