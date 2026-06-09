"""
Логика тарифов Free и Pro: пробный период, лимиты, эффективный план.
"""
from __future__ import annotations

from datetime import timedelta

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

PLAN_FREE = 'free'
PLAN_PRO = 'pro'

PLAN_CHOICES = [
    (PLAN_FREE, 'Free'),
    (PLAN_PRO, 'Pro'),
]

GRANTED_TRIAL = 'trial'
GRANTED_ADMIN = 'admin'
GRANTED_PAYMENT = 'payment'

GRANTED_CHOICES = [
    (GRANTED_TRIAL, 'Пробный период'),
    (GRANTED_ADMIN, 'Вручную (админка)'),
    (GRANTED_PAYMENT, 'Оплата'),
]

TRIAL_DAYS = 14

# Суммы в копейках (должны совпадать с app/pages/payment.vue)
SUBSCRIPTION_PRICE_KOPECKS = {
    'month': 50000,
    'year': 480000,
}

SUBSCRIPTION_PERIOD_DAYS = {
    'month': 30,
    'year': 365,
}

LIMITS = {
    PLAN_FREE: {
        'max_customers': 50,
        'max_bookings_per_month': 10,
        'max_services': 5,
    },
    PLAN_PRO: {
        'max_customers': 1500,
        'max_bookings_per_month': 150,
        'max_services': 15,
    },
}

PLAN_LABELS = {
    PLAN_FREE: 'Free',
    PLAN_PRO: 'Pro',
}


def get_effective_plan(user) -> str:
    """Активный тариф с учётом срока действия Pro."""
    if user.subscription_plan != PLAN_PRO:
        return PLAN_FREE
    if user.subscription_expires_at is None:
        return PLAN_PRO
    if timezone.now() < user.subscription_expires_at:
        return PLAN_PRO
    return PLAN_FREE


def get_limits(user) -> dict:
    return LIMITS[get_effective_plan(user)].copy()


def days_remaining(user) -> int | None:
    if user.subscription_plan != PLAN_PRO or not user.subscription_expires_at:
        return None
    expires = timezone.localtime(user.subscription_expires_at).date()
    today = timezone.localdate()
    return max(0, (expires - today).days)


def activate_pro_from_payment(user, billing_period: str, *, save: bool = True) -> None:
    """Продлевает или активирует Pro после успешной оплаты."""
    if billing_period not in SUBSCRIPTION_PERIOD_DAYS:
        raise ValueError(f'Unknown billing period: {billing_period}')

    now = timezone.now()
    delta = timedelta(days=SUBSCRIPTION_PERIOD_DAYS[billing_period])

    if user.subscription_expires_at and user.subscription_expires_at > now:
        expires = user.subscription_expires_at + delta
        started = user.subscription_started_at or now
    else:
        expires = now + delta
        started = now

    user.subscription_plan = PLAN_PRO
    user.subscription_expires_at = expires
    user.subscription_started_at = started
    user.subscription_granted_via = GRANTED_PAYMENT
    if save:
        user.save(
            update_fields=[
                'subscription_plan',
                'subscription_expires_at',
                'subscription_started_at',
                'subscription_granted_via',
            ]
        )


def start_pro_trial(user, *, save: bool = True) -> None:
    """14 дней Pro при регистрации."""
    now = timezone.now()
    user.subscription_plan = PLAN_PRO
    user.subscription_expires_at = now + timedelta(days=TRIAL_DAYS)
    user.subscription_started_at = now
    user.subscription_granted_via = GRANTED_TRIAL
    if save:
        user.save(
            update_fields=[
                'subscription_plan',
                'subscription_expires_at',
                'subscription_started_at',
                'subscription_granted_via',
            ]
        )


def require_pro_subscription(user) -> None:
    """Аналитика и другие Pro-функции: только при активном тарифе Pro."""
    if get_effective_plan(user) != PLAN_PRO:
        raise PermissionDenied(
            detail=(
                'Аналитика доступна на тарифе Pro. '
                'Оформите или продлите подписку на странице тарифов.'
            ),
            code='subscription_required',
        )


def build_subscription_payload(user) -> dict:
    effective = get_effective_plan(user)
    expires_at = user.subscription_expires_at
    remaining = days_remaining(user)
    limits = get_limits(user)

    is_trial = (
        user.subscription_granted_via == GRANTED_TRIAL
        and user.subscription_plan == PLAN_PRO
        and effective == PLAN_PRO
    )

    return {
        'plan': user.subscription_plan,
        'effectivePlan': effective,
        'planLabel': PLAN_LABELS[effective],
        'storedPlanLabel': PLAN_LABELS.get(user.subscription_plan, user.subscription_plan),
        'expiresAt': expires_at.isoformat() if expires_at else None,
        'startedAt': user.subscription_started_at.isoformat() if user.subscription_started_at else None,
        'isActive': effective == PLAN_PRO,
        'isTrial': is_trial,
        'grantedVia': user.subscription_granted_via or None,
        'daysRemaining': remaining,
        'limits': {
            'maxCustomers': limits['max_customers'],
            'maxBookingsPerMonth': limits['max_bookings_per_month'],
            'maxServices': limits['max_services'],
        },
    }


def _limit_error(resource: str, limit: int, plan_label: str) -> None:
    raise ValidationError({
        'detail': (
            f'Лимит тарифа {plan_label}: не более {limit} {resource}. '
            'Перейдите на Pro или продлите подписку на странице тарифов.'
        ),
        'code': 'subscription_limit',
    })


def check_customer_limit(user, *, additional: int = 1) -> None:
    from bookings.models import Customer

    limits = get_limits(user)
    count = Customer.objects.filter(user=user).count()
    if count + additional > limits['max_customers']:
        _limit_error('клиентов', limits['max_customers'], PLAN_LABELS[get_effective_plan(user)])


def check_service_limit(user, *, additional: int = 1) -> None:
    from bookings.models import Service

    limits = get_limits(user)
    count = Service.objects.filter(user=user).count()
    if count + additional > limits['max_services']:
        _limit_error('услуг', limits['max_services'], PLAN_LABELS[get_effective_plan(user)])


def check_booking_limit(user, *, additional: int = 1) -> None:
    from bookings.models import Booking

    limits = get_limits(user)
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if month_start.month == 12:
        next_month = month_start.replace(year=month_start.year + 1, month=1)
    else:
        next_month = month_start.replace(month=month_start.month + 1)

    count = (
        Booking.objects.filter(
            user=user,
            created_at__gte=month_start,
            created_at__lt=next_month,
        )
        .exclude(status='cancelled')
        .count()
    )
    if count + additional > limits['max_bookings_per_month']:
        _limit_error(
            'бронирований в месяц',
            limits['max_bookings_per_month'],
            PLAN_LABELS[get_effective_plan(user)],
        )
