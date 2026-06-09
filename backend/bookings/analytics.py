"""Расчёт метрик аналитики для личного кабинета."""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, Min, Sum

from .models import Booking


def _active_bookings_for_user(user):
    return Booking.objects.filter(user=user).exclude(status='cancelled')


def count_new_clients(user, start: date, end: date) -> int:
    """
    Клиенты, у которых первая (не отменённая) запись попадает в [start, end].
    """
    if start > end:
        return 0

    first_dates = (
        _active_bookings_for_user(user)
        .values('customer_id')
        .annotate(first_date=Min('date'))
    )

    return sum(
        1
        for row in first_dates
        if row['first_date'] is not None and start <= row['first_date'] <= end
    )


def previous_period(start: date, end: date) -> tuple[date, date]:
    """Предыдущий интервал той же длины, сразу перед start."""
    length_days = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=length_days - 1)
    return prev_start, prev_end


def variation_percent(current: int, previous: int) -> int:
    if previous == 0:
        return 100 if current > 0 else 0
    return round((current - previous) / previous * 100)


def _metric_with_comparison(user, start: date, end: date, counter) -> dict:
    current = counter(user, start, end)
    prev_start, prev_end = previous_period(start, end)
    previous = counter(user, prev_start, prev_end)
    return {
        'value': current,
        'variation': variation_percent(current, previous),
        'previousValue': previous,
    }


def count_regular_clients(user, start: date, end: date) -> int:
    """
    Постоянные клиенты за период: были на приёме в [start, end],
    первая запись была раньше start (не впервые в этом периоде),
    всего более 2 визитов (3+ неотменённых записей).
    """
    if start > end:
        return 0

    bookings = _active_bookings_for_user(user)
    in_period_ids = set(
        bookings.filter(date__gte=start, date__lte=end)
        .values_list('customer_id', flat=True)
        .distinct()
    )
    if not in_period_ids:
        return 0

    customer_stats = (
        bookings.filter(customer_id__in=in_period_ids)
        .values('customer_id')
        .annotate(total_count=Count('id'), first_date=Min('date'))
    )

    return sum(
        1
        for row in customer_stats
        if row['total_count'] > 2
        and row['first_date'] is not None
        and row['first_date'] < start
    )


def new_clients_metric(user, start: date, end: date) -> dict:
    return _metric_with_comparison(user, start, end, count_new_clients)


def regular_clients_metric(user, start: date, end: date) -> dict:
    return _metric_with_comparison(user, start, end, count_regular_clients)


def count_bookings(user, start: date, end: date) -> int:
    """Все неотменённые записи с датой приёма в [start, end]."""
    if start > end:
        return 0
    return _active_bookings_for_user(user).filter(date__gte=start, date__lte=end).count()


def bookings_metric(user, start: date, end: date) -> dict:
    return _metric_with_comparison(user, start, end, count_bookings)


def count_completed_bookings(user, start: date, end: date) -> int:
    """Записи, отмеченные исполнителем как оказанные (status=completed) в [start, end]."""
    if start > end:
        return 0
    return (
        Booking.objects.filter(user=user, status='completed')
        .filter(date__gte=start, date__lte=end)
        .count()
    )


def completed_bookings_metric(user, start: date, end: date) -> dict:
    return _metric_with_comparison(user, start, end, count_completed_bookings)


def _start_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _bucket_key(d: date, period: str) -> date:
    if period == 'weekly':
        return _start_of_week(d)
    if period == 'monthly':
        return d.replace(day=1)
    return d


def _iter_bucket_dates(start: date, end: date, period: str):
    if start > end:
        return

    if period == 'weekly':
        current = _start_of_week(start)
        last = _start_of_week(end)
        while current <= last:
            yield current
            current += timedelta(days=7)
        return

    if period == 'monthly':
        current = start.replace(day=1)
        while current <= end:
            yield current
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        return

    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _revenue_bookings_in_range(user, start: date, end: date, mode: str):
    """
    actual — только completed (фактический доход).
    potential — все записи, включая отменённые и без отметки «оказана».
    """
    qs = Booking.objects.filter(user=user, date__gte=start, date__lte=end).select_related('service')
    if mode == 'potential':
        return qs
    return qs.filter(status='completed')


def revenue_chart(user, start: date, end: date, period: str, mode: str = 'actual') -> dict:
    """
    Сумма цен услуг (service.price) по bucket'ам периода.
    mode=actual — завершённые; mode=potential — все записи в диапазоне.
    """
    if start > end:
        return {'total': 0.0, 'points': [], 'mode': mode}

    if period not in ('daily', 'weekly', 'monthly'):
        period = 'daily'

    if mode not in ('actual', 'potential'):
        mode = 'actual'

    amounts: dict[date, Decimal] = defaultdict(lambda: Decimal('0'))

    for booking in _revenue_bookings_in_range(user, start, end, mode):
        if not booking.service_id or booking.service is None:
            continue
        key = _bucket_key(booking.date, period)
        amounts[key] += booking.service.price

    points = []
    total = Decimal('0')
    for bucket_date in _iter_bucket_dates(start, end, period):
        amount = amounts.get(bucket_date, Decimal('0'))
        total += amount
        points.append({
            'date': bucket_date.isoformat(),
            'amount': float(amount),
        })

    return {
        'total': float(total),
        'points': points,
        'mode': mode,
    }


def _bookings_in_period(user, start: date, end: date):
    """Записи в периоде без отменённых (как в карточке «Записи»)."""
    if start > end:
        return Booking.objects.none()
    return (
        Booking.objects.filter(user=user, date__gte=start, date__lte=end)
        .exclude(status='cancelled')
        .select_related('service')
    )


def _breakdown_items(queryset, value_field: str) -> list[dict]:
    rows = list(queryset)
    items = []
    for row in rows:
        label = row.get('service__name') or 'Без названия'
        raw = row[value_field]
        if value_field == 'count':
            value = int(raw or 0)
        else:
            value = float(raw or 0)
        if value <= 0:
            continue
        items.append({'label': label, 'value': value})
    return items


def services_breakdown(user, start: date, end: date) -> dict:
    """
    Круговые диаграммы: число записей по услугам и доход (completed) по услугам.
    """
    base = _bookings_in_period(user, start, end)

    by_count = (
        base.values('service__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    booking_items = _breakdown_items(by_count, 'count')
    bookings_total = sum(i['value'] for i in booking_items)

    by_revenue = (
        base.filter(status='completed')
        .values('service__name')
        .annotate(amount=Sum('service__price'))
        .order_by('-amount')
    )
    revenue_items = _breakdown_items(by_revenue, 'amount')
    revenue_total = sum(i['value'] for i in revenue_items)

    return {
        'bookingsByService': {
            'total': bookings_total,
            'items': booking_items,
        },
        'revenueByService': {
            'total': revenue_total,
            'items': revenue_items,
        },
    }
