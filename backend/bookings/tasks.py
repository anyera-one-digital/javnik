"""
Celery задачи для приложения Bookly.
"""
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_email_task(subject, message, recipient_list, html_message=None):
    """
    Отправка email в фоне через Celery.
    
    Usage:
        send_email_task.delay(
            subject='Тема письма',
            message='Текст письма',
            recipient_list=['user@example.com'],
            html_message='<p>HTML текст</p>'
        )
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Email успешно отправлен: {recipient_list}')
        return {'status': 'success', 'recipients': recipient_list}
    except Exception as e:
        logger.error(f'Ошибка отправки email: {e}')
        return {'status': 'failed', 'error': str(e)}


@shared_task
def send_booking_confirmation_email(booking_id, customer_email):
    """
    Отправка подтверждения бронирования клиенту.
    
    Usage:
        send_booking_confirmation_email.delay(booking_id=1, customer_email='user@example.com')
    """
    from bookings.models import Booking
    
    try:
        booking = Booking.objects.select_related('service', 'customer').get(id=booking_id)
        subject = f'Подтверждение бронирования #{booking.id}'
        message = f'''
Здравствуйте, {booking.customer.name}!

Ваше бронирование подтверждено:

Услуга: {booking.service.name}
Дата: {booking.date.strftime('%d.%m.%Y')}
Время: {booking.start_time.strftime('%H:%M')}
Длительность: {booking.service.duration} мин.
Цена: {booking.service.price} ₽

До встречи!
        '''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer_email],
            fail_silently=False,
        )
        logger.info(f'Подтверждение бронирования #{booking_id} отправлено на {customer_email}')
        return {'status': 'success', 'booking_id': booking_id}
    except Booking.DoesNotExist:
        logger.error(f'Бронирование #{booking_id} не найдено')
        return {'status': 'failed', 'error': 'Booking not found'}
    except Exception as e:
        logger.error(f'Ошибка отправки подтверждения: {e}')
        return {'status': 'failed', 'error': str(e)}


@shared_task
def send_email_verification_code(user_id, code):
    """
    Отправка кода подтверждения email.
    
    Usage:
        send_email_verification_code.delay(user_id=1, code='123456')
    """
    from accounts.models import User
    
    try:
        user = User.objects.get(id=user_id)
        subject = 'Код подтверждения email'
        message = f'''
Здравствуйте, {user.username}!

Ваш код подтверждения email: {code}

Введите этот код в форме подтверждения.
Код действителен в течение 15 минут.
        '''
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info(f'Код подтверждения отправлен пользователю {user.email}')
        return {'status': 'success', 'user_id': user_id}
    except User.DoesNotExist:
        logger.error(f'Пользователь #{user_id} не найден')
        return {'status': 'failed', 'error': 'User not found'}
    except Exception as e:
        logger.error(f'Ошибка отправки кода: {e}')
        return {'status': 'failed', 'error': str(e)}
