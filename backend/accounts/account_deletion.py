"""Полное удаление аккаунта пользователя и связанных данных."""

from __future__ import annotations

from django.db import transaction

from bookings.models import Booking, Customer, Service, ServiceImage

ACTIVE_BOOKING_STATUSES = ('pending', 'confirmed')


def count_active_bookings(user) -> int:
    return Booking.objects.filter(
        user=user,
        status__in=ACTIVE_BOOKING_STATUSES,
    ).count()


def can_delete_account(user) -> bool:
    return count_active_bookings(user) == 0


def _delete_user_files(user) -> None:
    if user.avatar:
        user.avatar.delete(save=False)

    for customer in Customer.objects.filter(user=user):
        if customer.avatar:
            customer.avatar.delete(save=False)

    for service in Service.objects.filter(user=user):
        if service.cover_image:
            service.cover_image.delete(save=False)
        for image in ServiceImage.objects.filter(service=service):
            if image.image:
                image.image.delete(save=False)


@transaction.atomic
def delete_user_account(user) -> None:
    if not can_delete_account(user):
        raise ValueError('active_bookings')

    _delete_user_files(user)
    user.delete()
