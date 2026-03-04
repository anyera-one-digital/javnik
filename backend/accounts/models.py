from django.contrib.auth.models import AbstractUser
from django.db import models


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
