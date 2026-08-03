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
    Распределение записей и дохода по услугам.
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


def _sum_revenue(user, start: date, end: date, mode: str) -> float:
    total = Decimal('0')
    for booking in _revenue_bookings_in_range(user, start, end, mode):
        if not booking.service_id or booking.service is None:
            continue
        total += booking.service.price
    return float(total)


def revenue_metric(user, start: date, end: date) -> dict:
    current = _sum_revenue(user, start, end, 'actual')
    prev_start, prev_end = previous_period(start, end)
    previous = _sum_revenue(user, prev_start, prev_end, 'actual')
    return {
        'value': current,
        'variation': variation_percent(int(current), int(previous)),
        'previousValue': previous,
    }


def count_cancellations(user, start: date, end: date) -> int:
    if start > end:
        return 0
    return Booking.objects.filter(
        user=user, status='cancelled', date__gte=start, date__lte=end
    ).count()


def period_summary(user, start: date, end: date) -> dict:
    """Средний чек, отмены, повторные клиенты и подсказка по тренду."""
    completed = (
        Booking.objects.filter(user=user, status='completed', date__gte=start, date__lte=end)
        .select_related('service')
    )
    completed_count = completed.count()
    revenue = Decimal('0')
    for booking in completed:
        if booking.service_id and booking.service is not None:
            revenue += booking.service.price

    avg_check = float(revenue / completed_count) if completed_count else 0.0
    bookings_count = count_bookings(user, start, end)
    returning = count_regular_clients(user, start, end)
    cancellations = count_cancellations(user, start, end)

    trend_ready = bookings_count >= 5
    trend_hint = (
        None
        if trend_ready
        else f'Тренд появится после 5 записей'
    )

    return {
        'averageCheck': avg_check,
        'cancellations': cancellations,
        'returningClients': returning,
        'bookingsCount': bookings_count,
        'trendReady': trend_ready,
        'trendHint': trend_hint,
    }


def clients_breakdown(user, start: date, end: date) -> dict:
    """Новые vs повторные клиенты среди тех, кто был на приёме в периоде."""
    new_count = count_new_clients(user, start, end)
    returning = count_regular_clients(user, start, end)

    # Клиенты в периоде, которые не «новые» и не попали в «постоянные» (1–2 визита)
    bookings = _active_bookings_for_user(user)
    in_period_ids = set(
        bookings.filter(date__gte=start, date__lte=end)
        .values_list('customer_id', flat=True)
        .distinct()
    )
    total_clients = len(in_period_ids)
    # «Повторные» на карточке макета — все не-новые в периоде
    returning_in_period = max(0, total_clients - new_count)

    items = [
        {'label': 'Новые', 'value': new_count},
        {'label': 'Повторные', 'value': returning_in_period},
    ]
    return {
        'total': total_clients,
        'new': new_count,
        'returning': returning_in_period,
        'regular': returning,
        'items': items,
    }


def revenue_dual_chart(user, start: date, end: date, period: str) -> dict:
    """
    Столбцы: получено (completed) и ожидается (pending/confirmed).
    """
    if start > end:
        return {'totalReceived': 0.0, 'totalExpected': 0.0, 'points': []}

    if period not in ('daily', 'weekly', 'monthly'):
        period = 'daily'

    received: dict[date, Decimal] = defaultdict(lambda: Decimal('0'))
    expected: dict[date, Decimal] = defaultdict(lambda: Decimal('0'))

    qs = (
        Booking.objects.filter(user=user, date__gte=start, date__lte=end)
        .exclude(status='cancelled')
        .select_related('service')
    )
    for booking in qs:
        if not booking.service_id or booking.service is None:
            continue
        key = _bucket_key(booking.date, period)
        if booking.status == 'completed':
            received[key] += booking.service.price
        else:
            expected[key] += booking.service.price

    points = []
    total_received = Decimal('0')
    total_expected = Decimal('0')
    for bucket_date in _iter_bucket_dates(start, end, period):
        r = received.get(bucket_date, Decimal('0'))
        e = expected.get(bucket_date, Decimal('0'))
        total_received += r
        total_expected += e
        points.append({
            'date': bucket_date.isoformat(),
            'received': float(r),
            'expected': float(e),
        })

    return {
        'totalReceived': float(total_received),
        'totalExpected': float(total_expected),
        'points': points,
    }


def analytics_overview(user, start: date, end: date, period: str = 'daily') -> dict:
    """Сводка для верхнего блока аналитики (экран 1)."""
    bookings = bookings_metric(user, start, end)
    completed = completed_bookings_metric(user, start, end)
    success_total = bookings['value']
    success_rate = (
        round(100 * completed['value'] / success_total) if success_total else 0
    )

    return {
        'revenue': revenue_metric(user, start, end),
        'bookings': bookings,
        'newClients': new_clients_metric(user, start, end),
        'completedBookings': completed,
        'successRate': success_rate,
        'periodSummary': period_summary(user, start, end),
        'clientsBreakdown': clients_breakdown(user, start, end),
        'revenueByService': services_breakdown(user, start, end)['revenueByService'],
        'revenueChart': revenue_dual_chart(user, start, end, period),
        'previousRange': {
            'start': previous_period(start, end)[0].isoformat(),
            'end': previous_period(start, end)[1].isoformat(),
        },
    }


def _time_to_minutes(t) -> int:
    return t.hour * 60 + t.minute


def _day_available_minutes(sched) -> int:
    if sched.type != 'workday' or not sched.start_time or not sched.end_time:
        return 0
    total = _time_to_minutes(sched.end_time) - _time_to_minutes(sched.start_time)
    for br in sched.breaks or []:
        start_t = getattr(br, 'start_time', None)
        end_t = getattr(br, 'end_time', None)
        if start_t and end_t:
            total -= _time_to_minutes(end_t) - _time_to_minutes(start_t)
    return max(0, total)


def _booking_duration_minutes(booking) -> int:
    return max(0, _time_to_minutes(booking.end_time) - _time_to_minutes(booking.start_time))


WEEKDAY_LABELS_RU = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']


def load_analytics(user, start: date, end: date) -> dict:
    """
    Загрузка, свободные окна, heatmap, выводы, популярные услуги.
    """
    from .effective_schedule import get_effective_schedule_for_validation

    if start > end:
        return {
            'load': {'value': 0, 'variation': 0, 'previousValue': 0},
            'freeSlots': {'value': 0, 'variation': 0, 'previousValue': 0},
            'bookings': bookings_metric(user, start, end),
            'revenue': revenue_metric(user, start, end),
            'heatmap': {'hours': [], 'days': WEEKDAY_LABELS_RU, 'cells': []},
            'loadByDay': [],
            'insights': [],
            'popularServices': [],
            'previousRange': {
                'start': previous_period(start, end)[0].isoformat(),
                'end': previous_period(start, end)[1].isoformat(),
            },
        }

    def compute_load_and_free(s: date, e: date) -> tuple[float, int, list, dict]:
        available = 0
        booked = 0
        free_slots = 0
        # weekday -> (available_mins, booked_mins)
        by_weekday = {i: [0, 0] for i in range(7)}

        bookings = list(
            Booking.objects.filter(user=user, date__gte=s, date__lte=e)
            .exclude(status='cancelled')
            .select_related('service')
        )
        bookings_by_date: dict[date, list] = defaultdict(list)
        for b in bookings:
            bookings_by_date[b.date].append(b)
            booked += _booking_duration_minutes(b)
            by_weekday[b.date.weekday()][1] += _booking_duration_minutes(b)

        d = s
        while d <= e:
            sched = get_effective_schedule_for_validation(user, d)
            day_avail = _day_available_minutes(sched)
            available += day_avail
            by_weekday[d.weekday()][0] += day_avail

            if day_avail > 0 and sched.start_time and sched.end_time:
                start_h = sched.start_time.hour
                end_h = sched.end_time.hour
                if sched.end_time.minute > 0:
                    end_h += 1
                day_bookings = bookings_by_date.get(d, [])
                for hour in range(start_h, end_h):
                    slot_start = hour * 60
                    slot_end = (hour + 1) * 60
                    occupied = False
                    for b in day_bookings:
                        b_start = _time_to_minutes(b.start_time)
                        b_end = _time_to_minutes(b.end_time)
                        if b_start < slot_end and b_end > slot_start:
                            occupied = True
                            break
                    if not occupied:
                        free_slots += 1
            d += timedelta(days=1)

        load_pct = round(100 * booked / available) if available else 0
        load_by_day = []
        for i in range(7):
            avail_m, booked_m = by_weekday[i]
            pct = round(100 * booked_m / avail_m) if avail_m else 0
            load_by_day.append({
                'day': WEEKDAY_LABELS_RU[i],
                'weekday': i,
                'loadPercent': pct,
                'availableMinutes': avail_m,
                'bookedMinutes': booked_m,
            })
        return float(load_pct), free_slots, load_by_day, bookings_by_date

    load_pct, free_slots, load_by_day, _ = compute_load_and_free(start, end)
    prev_start, prev_end = previous_period(start, end)
    prev_load, prev_free, _, _ = compute_load_and_free(prev_start, prev_end)

    # Heatmap: часы 9–21 по умолчанию, сужаем по данным
    heat_counts = [[0 for _ in range(7)] for _ in range(24)]
    active = (
        Booking.objects.filter(user=user, date__gte=start, date__lte=end)
        .exclude(status='cancelled')
        .select_related('service')
    )
    booking_list = list(active)
    for b in booking_list:
        heat_counts[b.start_time.hour][b.date.weekday()] += 1

    hour_min, hour_max = 9, 19
    used_hours = [h for h in range(24) if any(heat_counts[h])]
    if used_hours:
        hour_min = min(9, min(used_hours))
        hour_max = max(19, max(used_hours))
    hour_min = max(0, min(hour_min, 23))
    hour_max = max(hour_min, min(hour_max, 23))

    hours = [f'{h:02d}:00' for h in range(hour_min, hour_max + 1)]
    cells = []
    max_cell = 1
    for h in range(hour_min, hour_max + 1):
        row = []
        for wd in range(7):
            c = heat_counts[h][wd]
            max_cell = max(max_cell, c)
            row.append(c)
        cells.append(row)

    insights = _build_insights(load_by_day, heat_counts, hour_min, hour_max, booking_list)

    popular = services_breakdown(user, start, end)
    popular_services = []
    # merge count + revenue by label
    revenue_map = {i['label']: i['value'] for i in popular['revenueByService']['items']}
    for item in popular['bookingsByService']['items']:
        popular_services.append({
            'name': item['label'],
            'bookings': int(item['value']),
            'revenue': float(revenue_map.get(item['label'], 0)),
        })

    return {
        'load': {
            'value': int(load_pct),
            'variation': int(load_pct) - int(prev_load),
            'previousValue': int(prev_load),
        },
        'freeSlots': {
            'value': free_slots,
            'variation': free_slots - prev_free,
            'previousValue': prev_free,
        },
        'bookings': bookings_metric(user, start, end),
        'revenue': revenue_metric(user, start, end),
        'heatmap': {
            'hours': hours,
            'days': WEEKDAY_LABELS_RU,
            'cells': cells,
            'max': max_cell,
        },
        'loadByDay': load_by_day,
        'insights': insights,
        'popularServices': popular_services,
        'previousRange': {
            'start': prev_start.isoformat(),
            'end': prev_end.isoformat(),
        },
    }


def _build_insights(load_by_day, heat_counts, hour_min, hour_max, bookings) -> list[dict]:
    insights = []
    if not bookings:
        insights.append({
            'icon': 'calendar',
            'text': 'Пока мало данных — выводы появятся после первых записей',
        })
        return insights

    day_verb = {
        'Пн': 'загружен',
        'Вт': 'загружен',
        'Ср': 'загружена',
        'Чт': 'загружен',
        'Пт': 'загружена',
        'Сб': 'загружена',
        'Вс': 'загружено',
    }
    day_full = {
        'Пн': 'понедельник',
        'Вт': 'вторник',
        'Ср': 'среду',
        'Чт': 'четверг',
        'Пт': 'пятницу',
        'Сб': 'субботу',
        'Вс': 'воскресенье',
    }
    day_prep = {
        'Пн': 'в',
        'Вт': 'во',
        'Ср': 'в',
        'Чт': 'в',
        'Пт': 'в',
        'Сб': 'в',
        'Вс': 'в',
    }

    work_days = [d for d in load_by_day if d['availableMinutes'] > 0]
    if work_days:
        busiest = max(work_days, key=lambda d: d['loadPercent'])
        day = busiest['day']
        insights.append({
            'icon': 'trending-up',
            'text': f'{day} {day_verb.get(day, "загружен")} на {busiest["loadPercent"]}%',
        })

        freest = min(work_days, key=lambda d: d['loadPercent'])
        free_hour = 15
        wd = freest['weekday']
        best = None
        for h in range(max(hour_min, 15), hour_max + 1):
            c = heat_counts[h][wd]
            if best is None or c <= best[1]:
                best = (h, c)
        if best:
            free_hour = best[0]
        insights.append({
            'icon': 'clock',
            'text': (
                f'Свободнее всего {day_prep.get(freest["day"], "в")} '
                f'{day_full.get(freest["day"], freest["day"])} после {free_hour:02d}:00'
            ),
        })

    long_evening = 0
    long_total = 0
    for b in bookings:
        duration = _booking_duration_minutes(b)
        if duration >= 75:
            long_total += 1
            if b.start_time.hour >= 17:
                long_evening += 1
    if long_total >= 2 and long_evening >= long_total / 2:
        insights.append({
            'icon': 'moon',
            'text': 'Длинные сессии чаще выбирают вечером',
        })
    elif bookings:
        peak_h, peak_c = 0, 0
        for h in range(24):
            c = sum(heat_counts[h])
            if c > peak_c:
                peak_h, peak_c = h, c
        if peak_c > 0:
            insights.append({
                'icon': 'activity',
                'text': f'Чаще всего записываются около {peak_h:02d}:00',
            })

    return insights[:3]
