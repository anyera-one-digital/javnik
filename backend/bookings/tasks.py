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


@shared_task
def send_new_booking_notification_to_staff(booking_id):
    """
    Отправка уведомления сотруднику о новой заявке на бронь.

    Usage:
        send_new_booking_notification_to_staff.delay(booking_id=1)
    """
    from bookings.models import Booking

    try:
        booking = Booking.objects.select_related('service', 'customer', 'member', 'event').get(id=booking_id)
        user = booking.user

        subject = f'Новая заявка на бронь #{booking.id} от {booking.customer.name}'

        # Формируем контекст для письма
        service_name = booking.service.name if booking.service else (booking.event.name if booking.event else '—')
        member_name = booking.member.name if booking.member else '—'
        event_name = booking.event.name if booking.event else '—'

        message = f'''
Здравствуйте, {user.username}!

Вам поступила новая заявка на бронирование:

Клиент: {booking.customer.name}
Телефон: {booking.customer.phone or '—'}
Email: {booking.customer.email}

Услуга: {service_name}
Сотрудник: {member_name}
Событие: {event_name}
Дата: {booking.date.strftime('%d.%m.%Y')}
Время начала: {booking.start_time.strftime('%H:%M')}
Время окончания: {booking.end_time.strftime('%H:%M')}
Длительность: {int((booking.end_time.hour * 60 + booking.end_time.minute) - (booking.start_time.hour * 60 + booking.start_time.minute))} мин.

Статус: Ожидает подтверждения

Заметки: {booking.notes or '—'}

Пожалуйста, подтвердите или отклоните заявку в личном кабинете.
        '''

        # HTML версия письма
        html_message = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .info-block {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .info-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #888; }}
        .status {{ display: inline-block; padding: 5px 15px; background-color: #F59E0B; color: white; border-radius: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Новая заявка на бронь</h1>
        </div>
        <div class="content">
            <p>Здравствуйте, <strong>{user.username}</strong>!</p>
            <p>Вам поступила новая заявка на бронирование.</p>
            
            <div class="info-block">
                <h3>Информация о клиенте</h3>
                <div class="info-row"><span class="label">Имя:</span> {booking.customer.name}</div>
                <div class="info-row"><span class="label">Телефон:</span> {booking.customer.phone or '—'}</div>
                <div class="info-row"><span class="label">Email:</span> {booking.customer.email}</div>
            </div>
            
            <div class="info-block">
                <h3>Детали бронирования</h3>
                <div class="info-row"><span class="label">Услуга:</span> {service_name}</div>
                <div class="info-row"><span class="label">Сотрудник:</span> {member_name}</div>
                <div class="info-row"><span class="label">Событие:</span> {event_name}</div>
                <div class="info-row"><span class="label">Дата:</span> {booking.date.strftime('%d.%m.%Y')}</div>
                <div class="info-row"><span class="label">Время:</span> {booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}</div>
                <div class="info-row"><span class="label">Длительность:</span> {int((booking.end_time.hour * 60 + booking.end_time.minute) - (booking.start_time.hour * 60 + booking.start_time.minute))} мин.</div>
            </div>
            
            <div class="info-block">
                <h3>Статус</h3>
                <span class="status">Ожидает подтверждения</span>
                {f'<p><strong>Заметки:</strong> {booking.notes}</p>' if booking.notes else ''}
            </div>
            
            <p style="margin-top: 20px;">Пожалуйста, подтвердите или отклоните заявку в личном кабинете.</p>
        </div>
        <div class="footer">
            <p>Это письмо отправлено автоматически. Пожалуйста, не отвечайте на него.</p>
        </div>
    </div>
</body>
</html>
        '''

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Уведомление о новой заявке #{booking_id} отправлено сотруднику {user.email}')
        return {'status': 'success', 'booking_id': booking_id}
    except Booking.DoesNotExist:
        logger.error(f'Бронирование #{booking_id} не найдено')
        return {'status': 'failed', 'error': 'Booking not found'}
    except Exception as e:
        logger.error(f'Ошибка отправки уведомления: {e}')
        return {'status': 'failed', 'error': str(e)}


@shared_task
def send_booking_pending_notification(booking_id, customer_email):
    """
    Отправка уведомления клиенту о том, что заявка на бронь создана и ожидает подтверждения.

    Usage:
        send_booking_pending_notification.delay(booking_id=1, customer_email='user@example.com')
    """
    from bookings.models import Booking

    try:
        booking = Booking.objects.select_related('service', 'customer').get(id=booking_id)
        subject = f'Заявка на бронирование #{booking.id} создана и ожидает подтверждения'

        service_name = booking.service.name if booking.service else (booking.event.name if booking.event else '—')

        message = f'''
Здравствуйте, {booking.customer.name}!

Ваша заявка на бронирование создана и ожидает подтверждения:

Услуга: {service_name}
Дата: {booking.date.strftime('%d.%m.%Y')}
Время: {booking.start_time.strftime('%H:%M')}
Длительность: {int((booking.end_time.hour * 60 + booking.end_time.minute) - (booking.start_time.hour * 60 + booking.start_time.minute))} мин.

Статус: Ожидает подтверждения

Мы уведомим вас, как только сотрудник подтвердит вашу заявку.
        '''

        # HTML версия письма
        html_message = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .info-block {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .info-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #888; }}
        .status {{ display: inline-block; padding: 5px 15px; background-color: #F59E0B; color: white; border-radius: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Заявка на бронирование</h1>
        </div>
        <div class="content">
            <p>Здравствуйте, <strong>{booking.customer.name}</strong>!</p>
            <p>Ваша заявка на бронирование создана и ожидает подтверждения.</p>
            
            <div class="info-block">
                <h3>Детали бронирования</h3>
                <div class="info-row"><span class="label">Услуга:</span> {service_name}</div>
                <div class="info-row"><span class="label">Дата:</span> {booking.date.strftime('%d.%m.%Y')}</div>
                <div class="info-row"><span class="label">Время:</span> {booking.start_time.strftime('%H:%M')}</div>
                <div class="info-row"><span class="label">Длительность:</span> {int((booking.end_time.hour * 60 + booking.end_time.minute) - (booking.start_time.hour * 60 + booking.start_time.minute))} мин.</div>
            </div>
            
            <div class="info-block">
                <h3>Статус</h3>
                <span class="status">Ожидает подтверждения</span>
            </div>
            
            <p style="margin-top: 20px;">Мы уведомим вас, как только сотрудник подтвердит вашу заявку.</p>
        </div>
        <div class="footer">
            <p>Это письмо отправлено автоматически. Пожалуйста, не отвечайте на него.</p>
        </div>
    </div>
</body>
</html>
        '''

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Уведомление о заявке #{booking_id} отправлено клиенту {customer_email}')
        return {'status': 'success', 'booking_id': booking_id}
    except Booking.DoesNotExist:
        logger.error(f'Бронирование #{booking_id} не найдено')
        return {'status': 'failed', 'error': 'Booking not found'}
    except Exception as e:
        logger.error(f'Ошибка отправки уведомления: {e}')
        return {'status': 'failed', 'error': str(e)}


@shared_task
def send_booking_confirmed_notification(booking_id, customer_email):
    """
    Отправка уведомления клиенту о подтверждении бронирования.

    Usage:
        send_booking_confirmed_notification.delay(booking_id=1, customer_email='user@example.com')
    """
    from bookings.models import Booking

    try:
        booking = Booking.objects.select_related('service', 'customer', 'member').get(id=booking_id)
        subject = f'Бронирование #{booking.id} подтверждено!'

        service_name = booking.service.name if booking.service else (booking.event.name if booking.event else '—')
        member_name = booking.member.name if booking.member else '—'

        message = f'''
Здравствуйте, {booking.customer.name}!

Ваше бронирование подтверждено:

Услуга: {service_name}
Сотрудник: {member_name}
Дата: {booking.date.strftime('%d.%m.%Y')}
Время: {booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}
Длительность: {int((booking.end_time.hour * 60 + booking.end_time.minute) - (booking.start_time.hour * 60 + booking.start_time.minute))} мин.

Статус: Подтверждено

Ждём вас! Если у вас возникнут вопросы, пожалуйста, свяжитесь с нами.
        '''

        # HTML версия письма
        html_message = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #10B981; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .info-block {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .info-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #888; }}
        .status {{ display: inline-block; padding: 5px 15px; background-color: #10B981; color: white; border-radius: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✓ Бронирование подтверждено</h1>
        </div>
        <div class="content">
            <p>Здравствуйте, <strong>{booking.customer.name}</strong>!</p>
            <p>Ваше бронирование подтверждено.</p>
            
            <div class="info-block">
                <h3>Детали бронирования</h3>
                <div class="info-row"><span class="label">Услуга:</span> {service_name}</div>
                <div class="info-row"><span class="label">Сотрудник:</span> {member_name}</div>
                <div class="info-row"><span class="label">Дата:</span> {booking.date.strftime('%d.%m.%Y')}</div>
                <div class="info-row"><span class="label">Время:</span> {booking.start_time.strftime('%H:%M')} - {booking.end_time.strftime('%H:%M')}</div>
                <div class="info-row"><span class="label">Длительность:</span> {int((booking.end_time.hour * 60 + booking.end_time.minute) - (booking.start_time.hour * 60 + booking.start_time.minute))} мин.</div>
            </div>
            
            <div class="info-block">
                <h3>Статус</h3>
                <span class="status">✓ Подтверждено</span>
            </div>
            
            <p style="margin-top: 20px;">Ждём вас! Если у вас возникнут вопросы, пожалуйста, свяжитесь с нами.</p>
        </div>
        <div class="footer">
            <p>Это письмо отправлено автоматически. Пожалуйста, не отвечайте на него.</p>
        </div>
    </div>
</body>
</html>
        '''

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Подтверждение бронирования #{booking_id} отправлено клиенту {customer_email}')
        return {'status': 'success', 'booking_id': booking_id}
    except Booking.DoesNotExist:
        logger.error(f'Бронирование #{booking_id} не найдено')
        return {'status': 'failed', 'error': 'Booking not found'}
    except Exception as e:
        logger.error(f'Ошибка отправки подтверждения: {e}')
        return {'status': 'failed', 'error': str(e)}


@shared_task
def send_booking_rejected_notification(booking_id, customer_email):
    """
    Отправка уведомления клиенту об отклонении бронирования.

    Usage:
        send_booking_rejected_notification.delay(booking_id=1, customer_email='user@example.com')
    """
    from bookings.models import Booking

    try:
        booking = Booking.objects.select_related('service', 'customer').get(id=booking_id)
        subject = f'Бронирование #{booking.id} отклонено'

        service_name = booking.service.name if booking.service else (booking.event.name if booking.event else '—')

        message = f'''
Здравствуйте, {booking.customer.name}!

К сожалению, ваше бронирование отклонено:

Услуга: {service_name}
Дата: {booking.date.strftime('%d.%m.%Y')}
Время: {booking.start_time.strftime('%H:%M')}

Статус: Отклонено

Пожалуйста, выберите другое время или услугу. Приносим извинения за неудобства.
        '''

        # HTML версия письма
        html_message = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #EF4444; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .info-block {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        .info-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; color: #555; }}
        .footer {{ text-align: center; padding: 15px; font-size: 12px; color: #888; }}
        .status {{ display: inline-block; padding: 5px 15px; background-color: #EF4444; color: white; border-radius: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✕ Бронирование отклонено</h1>
        </div>
        <div class="content">
            <p>Здравствуйте, <strong>{booking.customer.name}</strong>!</p>
            <p>К сожалению, ваше бронирование отклонено.</p>
            
            <div class="info-block">
                <h3>Детали бронирования</h3>
                <div class="info-row"><span class="label">Услуга:</span> {service_name}</div>
                <div class="info-row"><span class="label">Дата:</span> {booking.date.strftime('%d.%m.%Y')}</div>
                <div class="info-row"><span class="label">Время:</span> {booking.start_time.strftime('%H:%M')}</div>
            </div>
            
            <div class="info-block">
                <h3>Статус</h3>
                <span class="status">✕ Отклонено</span>
            </div>
            
            <p style="margin-top: 20px;">Пожалуйста, выберите другое время или услугу. Приносим извинения за неудобства.</p>
        </div>
        <div class="footer">
            <p>Это письмо отправлено автоматически. Пожалуйста, не отвечайте на него.</p>
        </div>
    </div>
</body>
</html>
        '''

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[customer_email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Уведомление об отклонении бронирования #{booking_id} отправлено клиенту {customer_email}')
        return {'status': 'success', 'booking_id': booking_id}
    except Booking.DoesNotExist:
        logger.error(f'Бронирование #{booking_id} не найдено')
        return {'status': 'failed', 'error': 'Booking not found'}
    except Exception as e:
        logger.error(f'Ошибка отправки уведомления: {e}')
        return {'status': 'failed', 'error': str(e)}
