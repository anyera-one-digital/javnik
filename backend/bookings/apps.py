from django.apps import AppConfig


class BookingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'
    verbose_name = 'Бронирования'

    def ready(self):
        # График по умолчанию задаётся шаблоном в профиле (work_schedule_template);
        # явные записи WorkSchedule — только исключения на конкретные даты.
        pass
