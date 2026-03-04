from django.apps import AppConfig


class BookingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bookings'
    verbose_name = 'Бронирования'

    def ready(self):
        from django.db.models.signals import post_save
        from django.contrib.auth import get_user_model
        from .services import create_default_work_schedule

        def on_user_created(sender, instance, created, **kwargs):
            if created:
                create_default_work_schedule(instance)

        User = get_user_model()
        post_save.connect(on_user_created, sender=User)
