from django.contrib.auth.models import AbstractUser
from django.db import models

from .subscription import GRANTED_CHOICES, PLAN_CHOICES


class SpecialtyCategory(models.Model):
    """Категория специальностей (например: Бьюти сфера, Медицина)."""
    name = models.CharField(max_length=255, verbose_name='Название')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Категория специальностей'
        verbose_name_plural = 'Категории специальностей'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Specialty(models.Model):
    """Специальность (например: Парикмахер, Визажист)."""
    category = models.ForeignKey(
        SpecialtyCategory,
        on_delete=models.CASCADE,
        related_name='specialties',
        verbose_name='Категория'
    )
    name = models.CharField(max_length=255, verbose_name='Название')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Специальность'
        verbose_name_plural = 'Специальности'
        ordering = ['category', 'order', 'name']

    def __str__(self):
        return self.name


class User(AbstractUser):
    """
    Кастомная модель пользователя
    """
    email = models.EmailField(unique=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True, verbose_name='Телефон')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Аватар')
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='users',
        verbose_name='Специальность'
    )
    bio = models.TextField(blank=True, null=True, verbose_name='О себе')
    city = models.CharField(max_length=255, blank=True, null=True, verbose_name='Город')
    service_address = models.TextField(blank=True, null=True, verbose_name='Адрес оказания услуг')
    service_address_lat = models.FloatField(blank=True, null=True, verbose_name='Широта адреса')
    service_address_lon = models.FloatField(blank=True, null=True, verbose_name='Долгота адреса')
    is_email_verified = models.BooleanField(default=False, verbose_name='Email подтвержден')
    show_public_schedule = models.BooleanField(
        default=True,
        verbose_name='Показывать расписание на публичной странице',
    )
    show_public_reviews = models.BooleanField(
        default=True,
        verbose_name='Показывать отзывы на публичной странице',
    )
    show_public_portfolio = models.BooleanField(
        default=True,
        verbose_name='Показывать портфолио на публичной странице',
    )
    work_schedule_template = models.CharField(
        max_length=32,
        default='standard-5',
        verbose_name='Шаблон графика работы',
    )
    shift_cycle = models.CharField(
        max_length=8,
        default='2-2',
        blank=True,
        verbose_name='Цикл смены (для посменного шаблона)',
    )
    shift_anchor_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Дата опоры цикла смен',
    )
    subscription_plan = models.CharField(
        max_length=8,
        choices=PLAN_CHOICES,
        default='free',
        verbose_name='Тариф (назначенный)',
    )
    subscription_expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Pro действует до',
        help_text='Для Pro: дата окончания. Пусто — без срока (бессрочный Pro).',
    )
    subscription_started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Начало текущего периода Pro',
    )
    subscription_granted_via = models.CharField(
        max_length=16,
        choices=GRANTED_CHOICES,
        blank=True,
        default='',
        verbose_name='Источник Pro',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class SubscriptionPayment(models.Model):
    """Платёж за подписку Pro через Т‑Кассу (T‑Bank)."""

    STATUS_NEW = 'new'
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_REJECTED = 'rejected'
    STATUS_CANCELED = 'canceled'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Создан'),
        (STATUS_PENDING, 'Ожидает оплаты'),
        (STATUS_CONFIRMED, 'Оплачен'),
        (STATUS_REJECTED, 'Отклонён'),
        (STATUS_CANCELED, 'Отменён'),
    ]

    BILLING_MONTH = 'month'
    BILLING_YEAR = 'year'
    BILLING_CHOICES = [
        (BILLING_MONTH, 'Месяц'),
        (BILLING_YEAR, 'Год'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription_payments',
        verbose_name='Пользователь',
    )
    order_id = models.CharField(max_length=36, unique=True, verbose_name='OrderId')
    payment_id = models.CharField(max_length=32, blank=True, default='', verbose_name='PaymentId T‑Bank')
    amount = models.PositiveIntegerField(verbose_name='Сумма, коп.')
    billing_period = models.CharField(max_length=8, choices=BILLING_CHOICES, verbose_name='Период')
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        verbose_name='Статус',
    )
    payment_url = models.URLField(blank=True, default='', verbose_name='URL оплаты')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    paid_at = models.DateTimeField(blank=True, null=True, verbose_name='Оплачен')

    class Meta:
        verbose_name = 'Платёж подписки'
        verbose_name_plural = 'Платежи подписки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order_id} ({self.get_status_display()})'
