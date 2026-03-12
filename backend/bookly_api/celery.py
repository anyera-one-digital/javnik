import os

from celery import Celery
from celery.schedules import crontab

# Установка переменной окружения DJANGO_SETTINGS_MODULE
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookly_api.settings')

# Создание приложения Celery
app = Celery('bookly_api')

# Загрузка конфигурации из Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автообнаружение задач во всех установленных приложениях
app.autodiscover_tasks()


# Настройка периодических задач
app.conf.beat_schedule = {
    # Пример: запуск задачи каждые 5 минут
    # 'send-reminders-every-5-minutes': {
    #     'task': 'bookings.tasks.send_booking_reminders',
    #     'schedule': crontab(minute='*/5'),
    # },
    
    # Пример: ежедневная задача в 9:00
    # 'daily-cleanup-every-day': {
    #     'task': 'bookings.tasks.cleanup_old_bookings',
    #     'schedule': crontab(hour=9, minute=0),
    # },
}
