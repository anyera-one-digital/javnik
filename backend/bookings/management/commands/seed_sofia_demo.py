"""
Плотное демо на весь месяц для sofiyatest@javnik.ru.

  python manage.py seed_sofia_demo --reset
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from bookings.models import Booking, Customer, Event, Service, WorkBreak, WorkSchedule

EMAIL = 'sofiyatest@javnik.ru'

SERVICES = [
    {'name': 'Консультация 30 мин', 'description': 'Короткая консультация', 'duration': 30, 'price': Decimal('1500.00'), 'active': True},
    {'name': 'Индивидуальная сессия', 'description': 'Основная сессия 60 мин', 'duration': 60, 'price': Decimal('3500.00'), 'active': True},
    {'name': 'Расширенная сессия', 'description': 'Глубокая проработка 90 мин', 'duration': 90, 'price': Decimal('4800.00'), 'active': True},
    {'name': 'Экспресс-разбор', 'description': 'Быстрый разбор 45 мин', 'duration': 45, 'price': Decimal('2200.00'), 'active': True},
    {'name': 'Групповой практикум', 'description': 'Групповое занятие', 'duration': 120, 'price': Decimal('2000.00'), 'active': True},
    {'name': 'Архивная услуга (неактивна)', 'description': 'Неактивна для проверки фильтров', 'duration': 60, 'price': Decimal('1000.00'), 'active': False},
]

CUSTOMERS = [
    {'name': 'Анна Ковалёва', 'email': 'anna.kovaleva@example.com', 'phone': '+79031234501', 'status': 'vip', 'notes': 'VIP, утро'},
    {'name': 'Дмитрий Орлов', 'email': 'd.orlov@example.com', 'phone': '+79031234502', 'status': 'loyal', 'notes': 'Раз в 2 недели'},
    {'name': 'Елена Соколова', 'email': 'e.sokolova@example.com', 'phone': '+79031234503', 'status': 'regular', 'notes': None},
    {'name': 'Игорь Морозов', 'email': 'i.morozov@example.com', 'phone': '+79031234504', 'status': 'first-time', 'notes': 'Первый визит'},
    {'name': 'Мария Волкова', 'email': 'm.volkova@example.com', 'phone': '+79031234505', 'status': 'loyal', 'notes': 'Вечер'},
    {'name': 'Павел Новиков', 'email': 'p.novikov@example.com', 'phone': '+79031234506', 'status': 'regular', 'notes': None},
    {'name': 'Ольга Белова', 'email': 'o.belova@example.com', 'phone': '+79031234507', 'status': 'vip', 'notes': 'Только очно'},
    {'name': 'Сергей Кузнецов', 'email': 's.kuznetsov@example.com', 'phone': '+79031234508', 'status': 'regular', 'notes': 'Часто переносит'},
    {'name': 'Наталья Егорова', 'email': 'n.egorova@example.com', 'phone': '+79031234509', 'status': 'first-time', 'notes': 'Рекомендация'},
    {'name': 'Алексей Смирнов', 'email': 'a.smirnov@example.com', 'phone': '+79031234510', 'status': 'loyal', 'notes': None},
    {'name': 'Юлия Фёдорова', 'email': 'y.fedorova@example.com', 'phone': '+79031234511', 'status': 'regular', 'notes': 'ДЗ'},
    {'name': 'Кирилл Лебедев', 'email': 'k.lebedev@example.com', 'phone': '+79031234512', 'status': 'regular', 'notes': None},
]


def _end(start: time, minutes: int) -> time:
    return (datetime.combine(date.today(), start) + timedelta(minutes=minutes)).time()


class Command(BaseCommand):
    help = f'Наполняет демо-данными аккаунт {EMAIL} на весь текущий месяц'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Удалить прежние данные пользователя')
        parser.add_argument('--email', default=EMAIL)

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        email = options['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as exc:
            raise CommandError(f'Пользователь {email} не найден') from exc

        if options['reset']:
            Booking.objects.filter(user=user).delete()
            Event.objects.filter(user=user).delete()
            WorkSchedule.objects.filter(user=user).delete()
            Service.objects.filter(user=user).delete()
            Customer.objects.filter(user=user).delete()
            self.stdout.write('Старые данные удалены')
        elif Service.objects.filter(user=user).exists():
            raise CommandError('Уже есть услуги. Запустите с --reset')

        today = timezone.localdate()
        month_start = date(today.year, today.month, 1)
        month_end = date(today.year, today.month, monthrange(today.year, today.month)[1])

        services = [Service.objects.create(user=user, **spec) for spec in SERVICES]
        customers = [Customer.objects.create(user=user, **spec) for spec in CUSTOMERS]
        s30, s60, s90, s45, s120, _inactive = services

        # Слоты без пересечений (standard-5: 10:00–20:00)
        patterns = {
            0: [(time(10, 0), 1), (time(11, 30), 0), (time(14, 0), 3), (time(16, 0), 1), (time(17, 30), 2)],  # Mon heavy
            1: [(time(10, 0), 1), (time(12, 0), 3), (time(15, 0), 1), (time(17, 0), 0)],  # Tue
            2: [(time(10, 30), 3), (time(12, 0), 1), (time(14, 30), 2), (time(16, 30), 0)],  # Wed
            3: [(time(10, 0), 0), (time(11, 0), 1), (time(13, 0), 3), (time(15, 30), 1), (time(17, 0), 2)],  # Thu
            4: [(time(10, 0), 1), (time(11, 30), 0), (time(15, 0), 3)],  # Fri lighter
            5: [(time(11, 0), 1), (time(13, 0), 3)],  # Sat rare
            6: [],  # Sun empty gap
        }

        created = 0
        day = month_start
        day_i = 0
        while day <= month_end:
            slots = patterns[day.weekday()]
            # Каждый 3-й понедельник — полностью пустой (пробел)
            if day.weekday() == 0 and (day.day // 7) % 3 == 2:
                slots = []

            for slot_i, (start, svc_i) in enumerate(slots):
                svc = services[svc_i]
                cust = customers[(day_i * 5 + slot_i) % len(customers)]
                if day < today:
                    status = 'completed'
                elif day == today:
                    status = 'completed' if start < time(14, 0) else ('pending' if slot_i % 2 else 'confirmed')
                else:
                    status = 'pending' if (day_i + slot_i) % 5 == 0 else 'confirmed'

                Booking.objects.create(
                    user=user,
                    customer=cust,
                    service=svc,
                    date=day,
                    start_time=start,
                    end_time=_end(start, svc.duration),
                    status=status,
                    notes='Демо август',
                )
                created += 1

                if day > today and slot_i == 0 and day_i % 9 == 0:
                    Booking.objects.create(
                        user=user,
                        customer=cust,
                        service=svc,
                        date=day,
                        start_time=time(9, 0),
                        end_time=_end(time(9, 0), svc.duration),
                        status='cancelled',
                        notes='Отменено (демо)',
                    )
                    created += 1

            day += timedelta(days=1)
            day_i += 1

        # Групповые события по средам 19:00
        events_n = 0
        d = month_start
        while d <= month_end:
            if d.weekday() == 2 and d >= today:
                Event.objects.create(
                    user=user,
                    service=s120,
                    name=f'Групповой практикум {d.strftime("%d.%m")}',
                    description='Демо событие',
                    date=d,
                    start_time=time(19, 0),
                    duration=120,
                    price=Decimal('2000.00'),
                    max_participants=8,
                    booked_slots=4,
                )
                events_n += 1
            d += timedelta(days=1)

        # Особые дни графика
        short_day = month_start + timedelta(days=2)
        while short_day.weekday() >= 5:
            short_day += timedelta(days=1)
        # Подрезать записи короткого дня под 11–16
        Booking.objects.filter(user=user, date=short_day).exclude(
            start_time__gte=time(11, 0), end_time__lte=time(16, 0)
        ).delete()
        for b in list(Booking.objects.filter(user=user, date=short_day)):
            if b.start_time < time(13, 30) and b.end_time > time(13, 0):
                b.delete()
        ws = WorkSchedule.objects.create(
            user=user, date=short_day, type='workday', start_time=time(11, 0), end_time=time(16, 0)
        )
        WorkBreak.objects.create(schedule=ws, start_time=time(13, 0), end_time=time(13, 30))

        vacation = date(today.year, today.month, 17) if today.month == 8 else month_start + timedelta(days=14)
        while vacation.weekday() != 0:
            vacation += timedelta(days=1)
        if vacation <= month_end:
            Booking.objects.filter(user=user, date=vacation).delete()
            WorkSchedule.objects.create(user=user, date=vacation, type='vacation')

        sick = vacation + timedelta(days=2)
        if sick <= month_end:
            Booking.objects.filter(user=user, date=sick).delete()
            WorkSchedule.objects.create(user=user, date=sick, type='sickleave')

        off = vacation - timedelta(days=3)
        while off.weekday() != 4:
            off -= timedelta(days=1)
        if month_start <= off <= month_end:
            Booking.objects.filter(user=user, date=off).delete()
            WorkSchedule.objects.create(user=user, date=off, type='nonworkday')

        by_status = {
            s: Booking.objects.filter(user=user, status=s).count()
            for s in ('pending', 'confirmed', 'completed', 'cancelled')
        }
        self.stdout.write(self.style.SUCCESS(
            f'Готово для {email}\n'
            f'  Месяц: {month_start} … {month_end}\n'
            f'  Услуги: {len(services)}, клиенты: {len(customers)}\n'
            f'  Записи: {Booking.objects.filter(user=user).count()} {by_status}\n'
            f'  События: {events_n}\n'
            f'  График: короткий {short_day}, выходной {off}, отпуск {vacation}, больничный {sick}'
        ))
