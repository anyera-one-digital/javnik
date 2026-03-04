"""
Отмена бронирований в статусе «ожидает подтверждения», созданных более 24 часов назад.
Запускать по крону раз в час, например: python manage.py cancel_expired_pending_bookings
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from bookings.models import Booking


class Command(BaseCommand):
    help = 'Отменяет брони со статусом pending, созданные более 24 часов назад'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать, какие брони были бы отменены',
        )

    def handle(self, *args, **options):
        deadline = timezone.now() - timedelta(hours=24)
        qs = Booking.objects.filter(status='pending', created_at__lt=deadline)
        count = qs.count()

        if options['dry_run']:
            self.stdout.write(f'Было бы отменено бронирований: {count}')
            for b in qs[:10]:
                self.stdout.write(f'  {b.id}: {b.customer.name} — {b.service.name} — {b.date}')
            if count > 10:
                self.stdout.write(f'  ... и ещё {count - 10}')
            return

        updated = qs.update(status='cancelled')
        self.stdout.write(self.style.SUCCESS(f'Отменено бронирований: {updated}'))
