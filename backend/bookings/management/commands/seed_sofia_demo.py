"""
Демо-данные на весь 2026 год для sofiyatest@javnik.ru.

Покрывает все статусы записей, все услуги, повторных/новых клиентов,
отмены, события и особые дни графика — для проверки аналитики.

  docker compose exec backend python manage.py seed_sofia_demo --reset
  docker compose exec backend python manage.py seed_sofia_demo --reset --year 2026
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from bookings.models import Booking, Customer, Event, Review, Service, ServiceImage, WorkBreak, WorkSchedule

EMAIL = 'sofiyatest@javnik.ru'

# Существующие файлы в media/services/portfolio/ (демо без внешних загрузок)
PORTFOLIO_FILES = [
    'services/portfolio/2d66b7814f1c5d7c0e23a0ca73a211b1.jpg',
    'services/portfolio/3190221369432145ab81f730867f761f.jpg',
    'services/portfolio/5ba0194886bda49e8c45963dab9550e7.jpg',
    'services/portfolio/6e4c20d8cb63f69684926f7b73ceb191.jpg',
    'services/portfolio/89d3964667b07e9416b0ea8dc1d43311.jpg',
    'services/portfolio/97e8c27d82f676a3769f24369df506b3.jpg',
    'services/portfolio/b0732477d8e0cea9e39aa31d2cf213a6.jpg',
    'services/portfolio/ce457a75ad525535f46d3d85b3e9f4ef.jpg',
    'services/portfolio/e785d386354d9e907f2500b6223ea1ca.jpg',
    'services/portfolio/f11694ba4beddb5ddcdea31400381a50.jpg',
]

# Разнообразные отзывы: (customer_idx, service_name|None, rating, comment, reply|None, days_ago)
REVIEW_SPECS = [
    (0, 'Индивидуальная сессия', 5, 'Очень тёплая атмосфера и понятные рекомендации. Уже после первой встречи стало легче.', 'Спасибо, Анна! Рада, что сессия была полезной 💛', 12),
    (1, 'Расширенная сессия', 5, 'Глубокий разбор, без воды. Дмитрий, рекомендую всем, кто хочет системный подход.', None, 18),
    (2, 'Консультация 30 мин', 4, 'Коротко и по делу. Хотелось бы чуть больше времени, но для старта отлично.', 'Спасибо за отзыв! Если нужно — запишитесь на расширенную сессию.', 25),
    (4, 'Онлайн-консультация', 5, 'Онлайн прошёл без технических сбоев, всё чётко. Удобно совмещать с работой.', None, 8),
    (5, 'Экспресс-разбор', 4, 'Быстро разобрали запрос. Получил конкретный план на неделю.', None, 33),
    (6, 'Разбор кейса', 5, 'Разбор кейса превзошёл ожидания. Теперь вижу, куда двигаться дальше.', 'Ольга, спасибо! Буду рада продолжить работу.', 5),
    (7, 'Групповой практикум', 3, 'Формат интересный, но группа большая — хотелось больше личного внимания.', 'Спасибо за честность. На следующих практикумах уменьшим состав.', 40),
    (8, 'Индивидуальная сессия', 5, 'Пришла по рекомендации и не пожалела. Очень бережный подход.', None, 15),
    (9, 'Расширенная сессия', 5, 'Профессионально, структурированно, с домашними заданиями. Вижу прогресс.', None, 22),
    (10, 'Консультация 30 мин', 4, 'Хорошая консультация. Записалась на полноценную сессию.', None, 3),
    (11, None, 5, 'В целом очень доволен работой специалиста. Всегда на связи и по делу.', None, 55),
    (12, 'Онлайн-консультация', 5, 'Онлайн даже удобнее очного для меня. София отлично держит фокус.', 'Татьяна, спасибо! До встречи на следующей сессии.', 9),
    (13, 'Экспресс-разбор', 4, 'Уложились в 45 минут и разобрали главное. Цена/качество ок.', None, 28),
    (14, 'Индивидуальная сессия', 5, 'Первый опыт терапии — и сразу попала к чуткому специалисту. Спасибо!', None, 2),
    (15, 'Разбор кейса', 5, 'Кейс разобрали по полочкам. Ушёл с ясным пониманием следующих шагов.', None, 17),
    (16, 'Групповой практикум', 4, 'Группа дала энергию и новые идеи. Хочу ещё раз прийти.', None, 11),
    (17, 'Консультация 30 мин', 5, 'Коротко, ясно, без давления. Идеально для знакомства.', None, 6),
    (0, 'Онлайн-консультация', 5, 'Повторная онлайн-сессия — так же качественно. Уже постоянный клиент.', None, 1),
    (3, 'Индивидуальная сессия', 4, 'Немного волновался перед визитом, но всё прошло спокойно и полезно.', 'Игорь, спасибо, что доверились! Жду вас снова.', 20),
    (6, 'Индивидуальная сессия', 5, 'Лучший специалист, с кем работала. Рекомендую коллегам.', None, 45),
]

SERVICES = [
    {
        'name': 'Консультация 30 мин',
        'description': 'Короткая консультация',
        'duration': 30,
        'price': Decimal('1500.00'),
        'active': True,
    },
    {
        'name': 'Индивидуальная сессия',
        'description': 'Основная сессия 60 мин',
        'duration': 60,
        'price': Decimal('3500.00'),
        'active': True,
    },
    {
        'name': 'Расширенная сессия',
        'description': 'Глубокая проработка 90 мин',
        'duration': 90,
        'price': Decimal('4800.00'),
        'active': True,
    },
    {
        'name': 'Экспресс-разбор',
        'description': 'Быстрый разбор 45 мин',
        'duration': 45,
        'price': Decimal('2200.00'),
        'active': True,
    },
    {
        'name': 'Групповой практикум',
        'description': 'Групповое занятие',
        'duration': 120,
        'price': Decimal('2000.00'),
        'active': True,
    },
    {
        'name': 'Онлайн-консультация',
        'description': 'Видеозвонок 50 мин',
        'duration': 50,
        'price': Decimal('2800.00'),
        'active': True,
    },
    {
        'name': 'Разбор кейса',
        'description': 'Разбор ситуации 75 мин',
        'duration': 75,
        'price': Decimal('4200.00'),
        'active': True,
    },
    {
        'name': 'Архивная услуга (неактивна)',
        'description': 'Неактивна для проверки фильтров',
        'duration': 60,
        'price': Decimal('1000.00'),
        'active': False,
    },
]

CUSTOMERS = [
    {'name': 'Анна Ковалёва', 'email': 'anna.kovaleva@example.com', 'phone': '+79031234501', 'status': 'vip', 'status_manual': True, 'notes': 'VIP, утро'},
    {'name': 'Дмитрий Орлов', 'email': 'd.orlov@example.com', 'phone': '+79031234502', 'status': 'loyal', 'status_manual': True, 'notes': 'Раз в 2 недели'},
    {'name': 'Елена Соколова', 'email': 'e.sokolova@example.com', 'phone': '+79031234503', 'status': 'regular', 'notes': None},
    {'name': 'Игорь Морозов', 'email': 'i.morozov@example.com', 'phone': '+79031234504', 'status': 'first-time', 'notes': 'Первый визит'},
    {'name': 'Мария Волкова', 'email': 'm.volkova@example.com', 'phone': '+79031234505', 'status': 'loyal', 'status_manual': True, 'notes': 'Вечер'},
    {'name': 'Павел Новиков', 'email': 'p.novikov@example.com', 'phone': '+79031234506', 'status': 'regular', 'notes': None},
    {'name': 'Ольга Белова', 'email': 'o.belova@example.com', 'phone': '+79031234507', 'status': 'vip', 'status_manual': True, 'notes': 'Только очно'},
    {'name': 'Сергей Кузнецов', 'email': 's.kuznetsov@example.com', 'phone': '+79031234508', 'status': 'regular', 'notes': 'Часто переносит'},
    {'name': 'Наталья Егорова', 'email': 'n.egorova@example.com', 'phone': '+79031234509', 'status': 'first-time', 'notes': 'Рекомендация'},
    {'name': 'Алексей Смирнов', 'email': 'a.smirnov@example.com', 'phone': '+79031234510', 'status': 'loyal', 'status_manual': True, 'notes': None},
    {'name': 'Юлия Фёдорова', 'email': 'y.fedorova@example.com', 'phone': '+79031234511', 'status': 'regular', 'notes': 'ДЗ'},
    {'name': 'Кирилл Лебедев', 'email': 'k.lebedev@example.com', 'phone': '+79031234512', 'status': 'regular', 'notes': None},
    {'name': 'Татьяна Романова', 'email': 't.romanova@example.com', 'phone': '+79031234513', 'status': 'vip', 'status_manual': True, 'notes': 'Онлайн'},
    {'name': 'Виктор Громов', 'email': 'v.gromov@example.com', 'phone': '+79031234514', 'status': 'regular', 'notes': None},
    {'name': 'Светлана Панина', 'email': 's.panina@example.com', 'phone': '+79031234515', 'status': 'first-time', 'notes': 'Новый клиент 2026'},
    {'name': 'Артём Зайцев', 'email': 'a.zaitsev@example.com', 'phone': '+79031234516', 'status': 'loyal', 'status_manual': True, 'notes': 'Вечерние слоты'},
    {'name': 'Ирина Медведева', 'email': 'i.medvedeva@example.com', 'phone': '+79031234517', 'status': 'regular', 'notes': None},
    {'name': 'Никита Соловьёв', 'email': 'n.solovyev@example.com', 'phone': '+79031234518', 'status': 'first-time', 'notes': 'Пришёл летом'},
]


def _end(start: time, minutes: int) -> time:
    return (datetime.combine(date.today(), start) + timedelta(minutes=minutes)).time()


def _seed_portfolio(services: list[Service]) -> int:
    """Привязать демо-фото ко всем активным услугам."""
    from pathlib import Path

    from django.conf import settings

    media_root = Path(settings.MEDIA_ROOT)
    available = [p for p in PORTFOLIO_FILES if (media_root / p).exists()]
    if not available:
        return 0

    created = 0
    active = [s for s in services if s.active]
    for svc_i, svc in enumerate(active):
        # 3–5 фото на услугу, со сдвигом чтобы набор отличался
        count = 3 + (svc_i % 3)
        for order in range(count):
            rel = available[(svc_i * 3 + order) % len(available)]
            img = ServiceImage(service=svc, order=order)
            img.image.name = rel
            img.save()
            created += 1
    return created


def _seed_reviews(user, customers: list[Customer], services: list[Service]) -> int:
    """Разнообразные отзывы с разным рейтингом и ответами."""
    by_name = {s.name: s for s in services}
    now = timezone.now()
    created = 0
    for cust_i, svc_name, rating, comment, reply, days_ago in REVIEW_SPECS:
        cust = customers[cust_i % len(customers)]
        svc = by_name.get(svc_name) if svc_name else None
        reply_author = None
        if reply:
            reply_author = (user.first_name or user.username or '').strip() or 'Специалист'
        review = Review(
            user=user,
            customer=cust,
            customer_name=cust.name,
            service=svc,
            rating=rating,
            comment=comment,
            reply=reply,
            reply_author=reply_author,
        )
        review.save()
        # backdate created_at
        Review.objects.filter(pk=review.pk).update(
            created_at=now - timedelta(days=days_ago, hours=(cust_i % 8))
        )
        created += 1
    return created


def _status_for_day(day: date, today: date, day_i: int, slot_i: int) -> str:
    """
    Распределение статусов для реалистичной аналитики.
    Прошлое — в основном completed + доля cancelled.
    Сегодня — смесь.
    Будущее — confirmed / pending / cancelled.
    """
    key = (day_i * 7 + slot_i) % 20

    if day < today:
        if key in (3, 11, 17):
            return 'cancelled'
        return 'completed'

    if day == today:
        if slot_i <= 1:
            return 'completed' if key % 3 else 'confirmed'
        if key % 4 == 0:
            return 'pending'
        if key % 5 == 0:
            return 'cancelled'
        return 'confirmed'

    if key in (2, 9, 14):
        return 'cancelled'
    if key in (0, 5, 10, 15):
        return 'pending'
    return 'confirmed'


# weekday -> list of (start, service_index among ACTIVE services 0..6)
# 0=30м, 1=60м, 2=90м, 3=45м, 4=120м, 5=онлайн, 6=кейс
WEEKDAY_PATTERNS = {
    0: [
        (time(10, 0), 1),
        (time(11, 30), 0),
        (time(13, 0), 3),
        (time(14, 30), 5),
        (time(16, 0), 1),
        (time(17, 30), 2),
    ],
    1: [
        (time(10, 0), 1),
        (time(12, 0), 3),
        (time(14, 0), 6),
    ],
    2: [
        (time(10, 30), 3),
        (time(12, 0), 1),
        (time(14, 0), 5),
        (time(15, 30), 0),
        (time(17, 0), 2),
        (time(19, 0), 4),
    ],
    3: [
        (time(10, 0), 0),
        (time(11, 0), 1),
        (time(13, 0), 3),
        (time(15, 0), 6),
        (time(17, 0), 2),
    ],
    4: [
        (time(10, 0), 1),
        (time(11, 30), 5),
        (time(15, 0), 3),
        (time(16, 30), 1),
        (time(18, 0), 2),
    ],
    5: [
        (time(11, 0), 1),
        (time(13, 0), 3),
    ],
    6: [],
}


class Command(BaseCommand):
    help = f'Наполняет демо-данными аккаунт {EMAIL} на весь указанный год'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Удалить прежние данные пользователя')
        parser.add_argument(
            '--enrich-only',
            action='store_true',
            help='Только портфолио и отзывы к уже существующим услугам/клиентам',
        )
        parser.add_argument('--email', default=EMAIL)
        parser.add_argument('--year', type=int, default=2026, help='Год наполнения (по умолчанию 2026)')

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        email = options['email']
        year = options['year']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist as exc:
            raise CommandError(f'Пользователь {email} не найден') from exc

        # Публичные блоки на странице профиля
        update_fields = []
        if hasattr(user, 'show_public_portfolio') and not user.show_public_portfolio:
            user.show_public_portfolio = True
            update_fields.append('show_public_portfolio')
        if hasattr(user, 'show_public_reviews') and not user.show_public_reviews:
            user.show_public_reviews = True
            update_fields.append('show_public_reviews')
        if update_fields:
            user.save(update_fields=update_fields)

        if options['enrich_only']:
            services = list(Service.objects.filter(user=user).order_by('sort_order', 'id'))
            customers = list(Customer.objects.filter(user=user).order_by('id'))
            if not services or not customers:
                raise CommandError('Нет услуг или клиентов. Сначала запустите seed без --enrich-only')
            ServiceImage.objects.filter(service__user=user).delete()
            Review.objects.filter(user=user).delete()
            n_img = _seed_portfolio(services)
            n_rev = _seed_reviews(user, customers, services)
            self.stdout.write(self.style.SUCCESS(
                f'Обогащение для {email}: портфолио {n_img} фото, отзывов {n_rev}'
            ))
            return

        if options['reset']:
            Booking.objects.filter(user=user).delete()
            Event.objects.filter(user=user).delete()
            WorkSchedule.objects.filter(user=user).delete()
            Review.objects.filter(user=user).delete()
            Service.objects.filter(user=user).delete()
            Customer.objects.filter(user=user).delete()
            self.stdout.write('Старые данные удалены')
        elif Service.objects.filter(user=user).exists():
            raise CommandError('Уже есть услуги. Запустите с --reset или --enrich-only')

        today = timezone.localdate()
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        services = [
            Service.objects.create(user=user, sort_order=i, **spec)
            for i, spec in enumerate(SERVICES)
        ]
        customers = [Customer.objects.create(user=user, **spec) for spec in CUSTOMERS]
        portfolio_n = _seed_portfolio(services)
        reviews_n = _seed_reviews(user, customers, services)
        active_services = [s for s in services if s.active]
        s_group = next(s for s in services if s.name == 'Групповой практикум')
        s_inactive = next(s for s in services if not s.active)

        created = 0
        day = year_start
        day_i = 0

        while day <= year_end:
            intensity = 1.0
            if day.month in (1, 8):
                intensity = 0.65
            elif day.month in (7, 12):
                intensity = 0.8

            slots = list(WEEKDAY_PATTERNS[day.weekday()])

            if day.weekday() == 0 and (day.isocalendar().week % 4) == 0:
                slots = []

            if intensity < 1.0 and slots:
                keep = max(1, int(round(len(slots) * intensity)))
                slots = slots[:keep]

            if day.weekday() == 6 and day_i % 5 == 0:
                slots = [(time(18, 0), 5)]

            for slot_i, (start, svc_i) in enumerate(slots):
                svc = active_services[svc_i % len(active_services)]
                pool_size = min(len(customers), 8 + (day.month * 2) // 3)
                cust = customers[(day_i * 5 + slot_i * 3) % pool_size]
                status = _status_for_day(day, today, day_i, slot_i)

                Booking.objects.create(
                    user=user,
                    customer=cust,
                    service=svc,
                    date=day,
                    start_time=start,
                    end_time=_end(start, svc.duration),
                    status=status,
                    notes=f'Демо {year}',
                )
                created += 1

            if day.weekday() < 5 and day_i % 10 == 3:
                Booking.objects.create(
                    user=user,
                    customer=customers[day_i % len(customers)],
                    service=active_services[day_i % len(active_services)],
                    date=day,
                    start_time=time(9, 0),
                    end_time=_end(time(9, 0), 30),
                    status='cancelled',
                    notes='Отмена до начала дня (демо)',
                )
                created += 1

            day += timedelta(days=1)
            day_i += 1

        # Гарантируем completed по каждой активной услуге
        guarantee_dates = [
            date(year, 2, 10),
            date(year, 3, 12),
            date(year, 4, 8),
            date(year, 5, 14),
            date(year, 6, 11),
            date(year, 7, 9),
            date(year, 9, 10),
        ]
        for i, svc in enumerate(active_services):
            d = guarantee_dates[i % len(guarantee_dates)]
            while d.weekday() >= 5:
                d += timedelta(days=1)
            for j in range(3):
                start = time(10 + j, 0)
                Booking.objects.create(
                    user=user,
                    customer=customers[(i * 3 + j) % len(customers)],
                    service=svc,
                    date=d + timedelta(weeks=j),
                    start_time=start,
                    end_time=_end(start, svc.duration),
                    status='completed',
                    notes=f'Гарантия услуги «{svc.name}»',
                )
                created += 1

        Booking.objects.create(
            user=user,
            customer=customers[0],
            service=s_inactive,
            date=date(year, 2, 5),
            start_time=time(12, 0),
            end_time=_end(time(12, 0), s_inactive.duration),
            status='completed',
            notes='Архивная услуга — completed',
        )
        Booking.objects.create(
            user=user,
            customer=customers[1],
            service=s_inactive,
            date=date(year, 11, 5),
            start_time=time(12, 0),
            end_time=_end(time(12, 0), s_inactive.duration),
            status='cancelled',
            notes='Архивная услуга — cancelled',
        )
        created += 2

        events_n = 0
        for month in range(1, 13):
            d = date(year, month, 1)
            wednesdays = 0
            while d.month == month:
                if d.weekday() == 2:
                    wednesdays += 1
                    if wednesdays == 2:
                        Event.objects.create(
                            user=user,
                            service=s_group,
                            name=f'Групповой практикум {d.strftime("%d.%m.%Y")}',
                            description='Демо событие',
                            date=d,
                            start_time=time(19, 0),
                            duration=120,
                            price=Decimal('2000.00'),
                            max_participants=8,
                            booked_slots=3 + (month % 5),
                        )
                        events_n += 1
                        break
                d += timedelta(days=1)

        special_notes = []
        for month, day_num, kind, extra in [
            (1, 7, 'nonworkday', None),
            (2, 10, 'workday', ('short', time(11, 0), time(16, 0))),
            (3, 9, 'vacation', None),
            (4, 15, 'sickleave', None),
            (5, 4, 'nonworkday', None),
            (6, 12, 'workday', ('short', time(12, 0), time(18, 0))),
            (8, 17, 'vacation', None),
            (9, 8, 'sickleave', None),
            (10, 14, 'workday', ('short', time(10, 0), time(15, 0))),
            (11, 4, 'nonworkday', None),
            (12, 28, 'vacation', None),
            (12, 29, 'vacation', None),
            (12, 30, 'vacation', None),
            (12, 31, 'vacation', None),
        ]:
            try:
                d = date(year, month, day_num)
            except ValueError:
                continue
            Booking.objects.filter(user=user, date=d).delete()
            if kind == 'workday' and extra and extra[0] == 'short':
                _, st, et = extra
                ws = WorkSchedule.objects.create(
                    user=user, date=d, type='workday', start_time=st, end_time=et
                )
                mid = time(st.hour + 1, 30) if st.hour + 1 < et.hour else None
                if mid and mid < et:
                    WorkBreak.objects.create(
                        schedule=ws,
                        start_time=mid,
                        end_time=_end(mid, 30),
                    )
                special_notes.append(f'короткий {d}')
            else:
                WorkSchedule.objects.create(user=user, date=d, type=kind)
                special_notes.append(f'{kind} {d}')

        by_status = {
            s: Booking.objects.filter(user=user, status=s).count()
            for s in ('pending', 'confirmed', 'completed', 'cancelled')
        }
        by_service = list(
            Booking.objects.filter(user=user, status='completed')
            .values_list('service__name')
            .order_by('service__name')
            .distinct()
        )

        self.stdout.write(self.style.SUCCESS(
            f'Готово для {email}\n'
            f'  Год: {year_start} … {year_end} (сегодня {today})\n'
            f'  Услуги: {len(services)} (активных {len(active_services)}), клиенты: {len(customers)}\n'
            f'  Портфолио: {portfolio_n} фото, отзывы: {reviews_n}\n'
            f'  Записи создано в цикле ≈{created}, всего в БД: {Booking.objects.filter(user=user).count()} {by_status}\n'
            f'  Completed по услугам ({len(by_service)}): {[n[0] for n in by_service]}\n'
            f'  События: {events_n}\n'
            f'  Особые дни: {", ".join(special_notes)}'
        ))
