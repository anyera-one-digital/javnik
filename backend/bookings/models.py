from django.db import models
from django.conf import settings


class Customer(models.Model):
    """
    Модель клиента
    """
    STATUS_CHOICES = [
        ('regular', 'Обычный'),
        ('loyal', 'Постоянный'),
        ('vip', 'VIP'),
        ('first-time', 'Первый раз'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customers',
        verbose_name='Владелец'
    )
    name = models.CharField(max_length=255, verbose_name='Имя')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Телефон')
    avatar = models.ImageField(upload_to='customers/', blank=True, null=True, verbose_name='Аватар')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='regular',
        verbose_name='Статус'
    )
    notes = models.TextField(blank=True, null=True, verbose_name='Заметки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']
        unique_together = [['user', 'email']]

    def __str__(self):
        return self.name


class Service(models.Model):
    """
    Модель услуги
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='Владелец'
    )
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    duration = models.IntegerField(verbose_name='Длительность (минуты)')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    cover_image = models.ImageField(upload_to='services/covers/', blank=True, null=True, verbose_name='Заглавное изображение')
    active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ServiceImage(models.Model):
    """
    Модель изображения для портфолио услуги
    """
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='portfolio_images',
        verbose_name='Услуга'
    )
    image = models.ImageField(upload_to='services/portfolio/', verbose_name='Изображение')
    order = models.IntegerField(default=0, verbose_name='Порядок сортировки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Изображение услуги'
        verbose_name_plural = 'Изображения услуг'
        ordering = ['order', 'created_at']

    def __str__(self):
        return f'{self.service.name} - Изображение {self.order}'


class Member(models.Model):
    """
    Модель сотрудника
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name='Владелец'
    )
    name = models.CharField(max_length=255, verbose_name='Имя')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Телефон')
    avatar = models.ImageField(upload_to='members/', blank=True, null=True, verbose_name='Аватар')
    position = models.CharField(max_length=255, blank=True, null=True, verbose_name='Должность')
    active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['-created_at']
        unique_together = [['user', 'email']]

    def __str__(self):
        return self.name


class Event(models.Model):
    """
    Модель события (групповое мероприятие)
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Владелец'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name='Услуга',
        blank=True,
        null=True
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='events',
        verbose_name='Сотрудник'
    )
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    date = models.DateField(verbose_name='Дата')
    start_time = models.TimeField(verbose_name='Время начала')
    duration = models.IntegerField(verbose_name='Длительность (минуты)')
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name='Стоимость')
    max_participants = models.IntegerField(default=0, verbose_name='Максимум участников')
    booked_slots = models.IntegerField(default=0, verbose_name='Забронировано мест')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['date', 'start_time']

    def __str__(self):
        return f'{self.name} - {self.date}'


class Booking(models.Model):
    """
    Модель бронирования
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Владелец'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Клиент'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Услуга'
    )
    member = models.ForeignKey(
        Member,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='bookings',
        verbose_name='Сотрудник'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='bookings',
        verbose_name='Событие'
    )
    date = models.DateField(verbose_name='Дата')
    start_time = models.TimeField(verbose_name='Время начала')
    end_time = models.TimeField(verbose_name='Время окончания')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    notes = models.TextField(blank=True, null=True, verbose_name='Заметки')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['date', 'start_time']

    def __str__(self):
        return f'{self.customer.name} - {self.service.name} - {self.date}'


class WorkBreak(models.Model):
    """
    Модель перерыва в рабочем дне
    """
    schedule = models.ForeignKey(
        'WorkSchedule',
        on_delete=models.CASCADE,
        related_name='breaks',
        verbose_name='График работы'
    )
    start_time = models.TimeField(verbose_name='Время начала перерыва')
    end_time = models.TimeField(verbose_name='Время окончания перерыва')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Перерыв'
        verbose_name_plural = 'Перерывы'
        ordering = ['start_time']

    def __str__(self):
        return f'{self.start_time} - {self.end_time}'


class WorkSchedule(models.Model):
    """
    Модель графика работы пользователя
    """
    TYPE_CHOICES = [
        ('workday', 'Рабочий день'),
        ('nonworkday', 'Нерабочий день'),
        ('sickleave', 'Больничный'),
        ('vacation', 'Отпуск'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='work_schedules',
        verbose_name='Владелец'
    )
    date = models.DateField(verbose_name='Дата')
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='workday',
        verbose_name='Тип дня'
    )
    start_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name='Время начала работы'
    )
    end_time = models.TimeField(
        blank=True,
        null=True,
        verbose_name='Время окончания работы'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'График работы'
        verbose_name_plural = 'Графики работы'
        ordering = ['date']
        unique_together = [['user', 'date']]

    def __str__(self):
        return f'{self.user.username} - {self.date} - {self.get_type_display()}'


class Review(models.Model):
    """
    Модель отзыва о пользователе/услуге
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Пользователь (кому оставлен отзыв)'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reviews',
        verbose_name='Клиент (кто оставил отзыв)'
    )
    customer_name = models.CharField(max_length=255, verbose_name='Имя клиента')
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reviews',
        verbose_name='Услуга'
    )
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name='Оценка (1-5)'
    )
    comment = models.TextField(blank=True, null=True, verbose_name='Комментарий')
    photos = models.JSONField(default=list, blank=True, verbose_name='Фотографии')
    reply = models.TextField(blank=True, null=True, verbose_name='Ответ специалиста')
    reply_author = models.CharField(max_length=255, blank=True, null=True, verbose_name='Автор ответа')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Автоматически заполняем customer_name из customer, если он указан и customer_name пустое
        if self.customer and (not self.customer_name or self.customer_name.strip() == ''):
            self.customer_name = self.customer.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.customer_name} - {self.user.username} - {self.rating} звезд'
