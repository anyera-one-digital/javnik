"""
Модели для редактируемого контента главной страницы лендинга.
"""
from django.db import models


class LandingHero(models.Model):
    """Блок «Главный экран» — заголовок и описание."""
    title = models.CharField(max_length=500, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    seo_title = models.CharField(max_length=255, blank=True, verbose_name='SEO заголовок')
    seo_description = models.TextField(blank=True, verbose_name='SEO описание')

    class Meta:
        verbose_name = 'Главный экран (Hero)'
        verbose_name_plural = 'Главный экран (Hero)'

    def __str__(self):
        return self.title[:50]


class LandingFAQItem(models.Model):
    """Вопрос-ответ."""
    block = models.ForeignKey('LandingFAQBlock', on_delete=models.CASCADE, related_name='items', verbose_name='Блок')
    label = models.CharField(max_length=500, verbose_name='Вопрос')
    content = models.TextField(verbose_name='Ответ')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Вопрос-ответ'
        verbose_name_plural = 'Вопросы-ответы'
        ordering = ['order']

    def __str__(self):
        return self.label[:50]


class LandingFAQBlock(models.Model):
    """Блок «Часто задаваемые вопросы»."""
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Блок «Вопросы-ответы»'
        verbose_name_plural = 'Блок «Вопросы-ответы»'

    def __str__(self):
        return self.title


class LegalPage(models.Model):
    """Юридические страницы: политика конфиденциальности, пользовательское соглашение."""

    SLUG_PRIVACY = 'privacy'
    SLUG_TERMS = 'terms'
    SLUG_CHOICES = [
        (SLUG_PRIVACY, 'Политика конфиденциальности'),
        (SLUG_TERMS, 'Пользовательское соглашение'),
    ]

    slug = models.SlugField(
        max_length=32,
        unique=True,
        choices=SLUG_CHOICES,
        verbose_name='Страница',
    )
    title = models.CharField(max_length=500, verbose_name='Заголовок')
    subtitle = models.CharField(max_length=500, blank=True, verbose_name='Подзаголовок')
    content = models.TextField(
        verbose_name='Содержимое (HTML)',
        help_text='HTML-разметка тела страницы (без заголовка h1). Допустимы теги: section, h2, p, ul, ol, li, a, strong, table.',
    )
    seo_title = models.CharField(max_length=255, blank=True, verbose_name='SEO заголовок')
    seo_description = models.TextField(blank=True, verbose_name='SEO описание')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Юридическая страница'
        verbose_name_plural = 'Юридические страницы'

    def __str__(self):
        return self.get_slug_display()
