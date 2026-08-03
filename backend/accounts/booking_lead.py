"""
Правила минимального срока до записи для клиентов (публичная запись).
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

from django.utils import timezone

LEAD_SAME_DAY_1H = 'same_day_1h'
LEAD_NEXT_DAY = 'next_day'
LEAD_SKIP_ONE = 'skip_one_day'
LEAD_SKIP_TWO = 'skip_two_days'

BOOKING_LEAD_CHOICES = [
    (LEAD_SAME_DAY_1H, 'За час'),
    (LEAD_NEXT_DAY, 'На следующий день'),
    (LEAD_SKIP_ONE, 'Через день'),
    (LEAD_SKIP_TWO, 'Через два дня'),
]

ALLOWED_BOOKING_LEADS = {c[0] for c in BOOKING_LEAD_CHOICES}
DEFAULT_BOOKING_LEAD = LEAD_SAME_DAY_1H

# Минимальный календарный сдвиг даты (для вариантов «на следующий день» и дальше)
LEAD_MIN_CALENDAR_DAYS = {
    LEAD_NEXT_DAY: 1,
    LEAD_SKIP_ONE: 2,
    LEAD_SKIP_TWO: 3,
}


def normalize_booking_lead(value: str | None) -> str:
    v = (value or '').strip()
    if v in ALLOWED_BOOKING_LEADS:
        return v
    return DEFAULT_BOOKING_LEAD


def earliest_bookable_date(lead: str, *, today: date | None = None) -> date:
    """Первая календарная дата, на которую клиент может записаться."""
    lead = normalize_booking_lead(lead)
    today = today or timezone.localdate()
    if lead == LEAD_SAME_DAY_1H:
        return today
    return today + timedelta(days=LEAD_MIN_CALENDAR_DAYS[lead])


def is_booking_datetime_allowed(
    lead: str,
    booking_date: date,
    booking_start: time,
    *,
    now: datetime | None = None,
) -> bool:
    """Проверка, что слот не раньше разрешённого горизонта записи."""
    lead = normalize_booking_lead(lead)
    now = timezone.localtime(now) if now else timezone.localtime()

    if lead == LEAD_SAME_DAY_1H:
        naive = datetime.combine(booking_date, booking_start)
        if timezone.is_naive(naive):
            slot_dt = timezone.make_aware(naive, timezone.get_current_timezone())
        else:
            slot_dt = naive
        return slot_dt >= now + timedelta(hours=1)

    return booking_date >= earliest_bookable_date(lead, today=now.date())


def booking_lead_error_message(lead: str) -> str:
    lead = normalize_booking_lead(lead)
    messages = {
        LEAD_SAME_DAY_1H: 'Запись возможна не раньше чем за час до начала.',
        LEAD_NEXT_DAY: 'Запись возможна только на следующий день или позже.',
        LEAD_SKIP_ONE: 'Запись возможна только через день или позже.',
        LEAD_SKIP_TWO: 'Запись возможна только через два дня или позже.',
    }
    return messages[lead]
