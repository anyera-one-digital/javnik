"""
Оплата подписки Pro через T‑Bank (Т‑Касса).
"""
from __future__ import annotations

import logging
import uuid

from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import SubscriptionPayment, User
from .subscription import SUBSCRIPTION_PRICE_KOPECKS, activate_pro_from_payment
from .tbank import TBankAPIError, init_payment, is_tbank_configured, verify_notification_token

logger = logging.getLogger(__name__)

TBANK_SUCCESS_STATUSES = frozenset({'CONFIRMED', 'AUTHORIZED'})


def _frontend_base_url() -> str:
    return getattr(settings, 'FRONTEND_BASE_URL', 'http://localhost:4000').rstrip('/')


def _notification_url() -> str:
    explicit = str(getattr(settings, 'TBANK_NOTIFICATION_URL', '') or '').strip()
    if explicit:
        return explicit
    api_public = str(getattr(settings, 'API_PUBLIC_BASE_URL', '') or '').strip()
    if api_public:
        return f'{api_public.rstrip("/")}/api/auth/payments/tbank/notification/'
    # Локально: Init проходит, webhook с интернета не дойдёт без ngrok
    if getattr(settings, 'DEBUG', False):
        return 'http://localhost:8000/api/auth/payments/tbank/notification/'
    return ''


def _payment_setup_error() -> tuple[str, str] | None:
    """Код и текст ошибки конфигурации или None, если всё ок для Init."""
    key = str(getattr(settings, 'TBANK_TERMINAL_KEY', '') or '').strip()
    password = str(getattr(settings, 'TBANK_PASSWORD', '') or '').strip()
    if not key or not password:
        return (
            'missing_tbank_credentials',
            'Не заданы TBANK_TERMINAL_KEY и TBANK_PASSWORD в backend/.env. '
            'Файл .env.example Django не читает — скопируйте значения в backend/.env '
            'и выполните: docker compose restart backend',
        )
    if not _notification_url():
        return (
            'missing_notification_url',
            'Не задан API_PUBLIC_BASE_URL или TBANK_NOTIFICATION_URL в backend/.env.',
        )
    return None


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def subscription_payment_init_view(request):
    """
    Создать платёж и вернуть URL формы T‑Bank.
    POST /api/auth/payments/subscription/init/
    Body: { "billing_period": "month" | "year" }
    """
    setup_error = _payment_setup_error()
    if setup_error:
        code, message = setup_error
        return Response(
            {'error': message, 'code': code},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    notification_url = _notification_url()

    billing_period = (request.data.get('billing_period') or '').strip()
    if billing_period not in SUBSCRIPTION_PRICE_KOPECKS:
        return Response(
            {'error': 'Укажите billing_period: month или year.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    amount = SUBSCRIPTION_PRICE_KOPECKS[billing_period]
    user: User = request.user
    order_id = uuid.uuid4().hex

    period_label = 'месяц' if billing_period == 'month' else 'год'
    description = f'Bookly Pro — подписка на {period_label}'

    payment = SubscriptionPayment.objects.create(
        user=user,
        order_id=order_id,
        amount=amount,
        billing_period=billing_period,
        status=SubscriptionPayment.STATUS_NEW,
    )

    success_url = f'{_frontend_base_url()}/payment/success?orderId={order_id}'
    fail_url = f'{_frontend_base_url()}/payment/fail?orderId={order_id}'

    try:
        tbank_response = init_payment(
            order_id=order_id,
            amount=amount,
            description=description,
            customer_key=str(user.id),
            success_url=success_url,
            fail_url=fail_url,
            notification_url=notification_url,
        )
    except TBankAPIError as exc:
        payment.status = SubscriptionPayment.STATUS_REJECTED
        payment.save(update_fields=['status'])
        return Response({'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as exc:
        logger.exception('T-Bank Init request failed')
        payment.status = SubscriptionPayment.STATUS_REJECTED
        payment.save(update_fields=['status'])
        return Response(
            {'error': 'Ошибка связи с платёжным сервисом. Попробуйте позже.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    payment.payment_id = str(tbank_response.get('PaymentId', '') or '')
    payment.payment_url = tbank_response.get('PaymentURL', '') or ''
    payment.status = SubscriptionPayment.STATUS_PENDING
    payment.save(update_fields=['payment_id', 'payment_url', 'status'])

    return Response(
        {
            'orderId': order_id,
            'paymentId': payment.payment_id,
            'paymentUrl': payment.payment_url,
            'amount': amount,
            'billingPeriod': billing_period,
        },
        status=status.HTTP_201_CREATED,
    )


@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def tbank_notification_view(request):
    """
    Webhook T‑Bank (NotificationURL).
    POST /api/auth/payments/tbank/notification/
    """
    if not is_tbank_configured():
        return Response('NOT CONFIGURED', status=status.HTTP_503_SERVICE_UNAVAILABLE)

    payload = request.data
    if not isinstance(payload, dict):
        return Response('INVALID', status=status.HTTP_400_BAD_REQUEST)

    if not verify_notification_token(payload, settings.TBANK_PASSWORD):
        logger.warning('T-Bank notification: invalid token for OrderId=%s', payload.get('OrderId'))
        return Response('INVALID TOKEN', status=status.HTTP_403_FORBIDDEN)

    order_id = payload.get('OrderId')
    if not order_id:
        return Response('OK')

    try:
        payment = SubscriptionPayment.objects.select_related('user').get(order_id=order_id)
    except SubscriptionPayment.DoesNotExist:
        logger.warning('T-Bank notification: unknown OrderId=%s', order_id)
        return Response('OK')

    tbank_status = (payload.get('Status') or '').upper()
    success_flag = payload.get('Success')

    if payment.status == SubscriptionPayment.STATUS_CONFIRMED:
        return Response('OK')

    if tbank_status in TBANK_SUCCESS_STATUSES and success_flag in (True, 'true', 'True', 1, '1'):
        payment.status = SubscriptionPayment.STATUS_CONFIRMED
        payment.payment_id = str(payload.get('PaymentId', payment.payment_id) or '')
        payment.paid_at = timezone.now()
        payment.save(update_fields=['status', 'payment_id', 'paid_at'])
        activate_pro_from_payment(payment.user, payment.billing_period)
        logger.info('Subscription activated for user %s, order %s', payment.user_id, order_id)
    elif tbank_status in ('REJECTED', 'CANCELED', 'REVERSED', 'REFUNDED'):
        payment.status = (
            SubscriptionPayment.STATUS_CANCELED
            if tbank_status == 'CANCELED'
            else SubscriptionPayment.STATUS_REJECTED
        )
        payment.save(update_fields=['status'])

    return Response('OK')
