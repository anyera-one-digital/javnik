"""
Модели для редактируемого контента главной страницы лендинга.
Каждый блок лендинга — отдельная модель с полями.
"""
from django.db import models


class LandingImage(models.Model):
    """Загруженные изображения для лендинга."""
    image = models.ImageField(upload_to='landing/', verbose_name='Изображение')
    alt_text = models.CharField(max_length=255, blank=True, verbose_name='Описание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    class Meta:
        verbose_name = 'Изображение лендинга'
        verbose_name_plural = 'Изображения лендинга'
        ordering = ['-created_at']

    def __str__(self):
        return self.alt_text or str(self.image.name)


# === 1. Hero (главный экран) ===
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


# === 2. Секции (для кого создан, вы больше никогда...) ===
class LandingSectionFeature(models.Model):
    """Пункт внутри секции."""
    section = models.ForeignKey('LandingSection', on_delete=models.CASCADE, related_name='features', verbose_name='Секция')
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    icon = models.CharField(max_length=100, default='i-lucide-circle', verbose_name='Иконка (например i-lucide-scissors)')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Пункт секции'
        verbose_name_plural = 'Пункты секции'
        ordering = ['order']

    def __str__(self):
        return self.name


class LandingSection(models.Model):
    """Блок секции (например «Для кого создан этот сервис», «Вы больше никогда...»)."""
    title = models.CharField(max_length=500, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    section_id = models.CharField(max_length=100, blank=True, verbose_name='ID для якоря')
    image = models.ImageField(upload_to='landing/sections/', blank=True, null=True, verbose_name='Изображение')
    image_url = models.URLField(max_length=500, blank=True, verbose_name='Или URL изображения')
    orientation = models.CharField(max_length=20, default='horizontal', choices=[('horizontal', 'Горизонтально'), ('vertical', 'Вертикально')], verbose_name='Ориентация')
    reverse = models.BooleanField(default=False, verbose_name='Порядок: картинка справа')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Секция (блок с картинкой и пунктами)'
        verbose_name_plural = 'Секции'
        ordering = ['order']

    def __str__(self):
        return self.title[:50]

    def get_image_url(self):
        if self.image:
            return self.image.url
        return self.image_url or ''


# === 3. Преимущества ===
class LandingFeatureItem(models.Model):
    """Пункт блока «Преимущества»."""
    block = models.ForeignKey('LandingFeatureBlock', on_delete=models.CASCADE, related_name='items', verbose_name='Блок')
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')
    icon = models.CharField(max_length=100, default='i-lucide-circle', verbose_name='Иконка')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Пункт преимущества'
        verbose_name_plural = 'Пункты преимуществ'
        ordering = ['order']

    def __str__(self):
        return self.title


class LandingFeatureBlock(models.Model):
    """Блок «Преимущества, которые вы оцените»."""
    headline = models.CharField(max_length=255, blank=True, verbose_name='Подзаголовок')
    title = models.CharField(max_length=500, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Блок «Преимущества»'
        verbose_name_plural = 'Блок «Преимущества»'

    def __str__(self):
        return self.title[:50]


# === 4. Отзывы ===
class LandingTestimonial(models.Model):
    """Отзыв в блоке «Истории успеха»."""
    quote = models.TextField(verbose_name='Цитата')
    user_name = models.CharField(max_length=255, verbose_name='Имя')
    user_description = models.CharField(max_length=255, verbose_name='Профессия/описание')
    user_avatar = models.ImageField(upload_to='landing/testimonials/', blank=True, null=True, verbose_name='Фото')
    user_avatar_url = models.URLField(max_length=500, blank=True, verbose_name='Или URL фото')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['order']

    def __str__(self):
        return self.user_name

    def get_avatar_url(self):
        if self.user_avatar:
            return self.user_avatar.url
        return self.user_avatar_url or ''


class LandingTestimonialBlock(models.Model):
    """Блок «Истории успеха» — заголовок и описание."""
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Блок «Истории успеха»'
        verbose_name_plural = 'Блок «Истории успеха»'

    def __str__(self):
        return self.title


# === 5. Тарифы ===
class LandingPricingPlanFeature(models.Model):
    """Пункт в тарифном плане."""
    plan = models.ForeignKey('LandingPricingPlan', on_delete=models.CASCADE, related_name='features', verbose_name='План')
    text = models.CharField(max_length=255, verbose_name='Пункт')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Пункт тарифа'
        verbose_name_plural = 'Пункты тарифов'
        ordering = ['order']

    def __str__(self):
        return self.text


class LandingPricingPlan(models.Model):
    """Тарифный план."""
    block = models.ForeignKey('LandingPricingBlock', on_delete=models.CASCADE, related_name='plans', verbose_name='Блок')
    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    price_month = models.CharField(max_length=50, verbose_name='Цена/месяц')
    price_year = models.CharField(max_length=50, verbose_name='Цена/год')
    button_label = models.CharField(max_length=100, default='Начать', verbose_name='Текст кнопки')
    highlight = models.BooleanField(default=False, verbose_name='Выделить')
    scale = models.BooleanField(default=False, verbose_name='Увеличить')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Тарифный план'
        verbose_name_plural = 'Тарифные планы'
        ordering = ['order']

    def __str__(self):
        return self.title


class LandingPricingBlock(models.Model):
    """Блок «План для каждой потребности»."""
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Блок «Тарифы»'
        verbose_name_plural = 'Блок «Тарифы»'

    def __str__(self):
        return self.title


# === 6. FAQ ===
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


# === 7. CTA (призыв к действию) ===
class LandingCTALink(models.Model):
    """Кнопка в блоке CTA."""
    block = models.ForeignKey('LandingCTA', on_delete=models.CASCADE, related_name='links', verbose_name='Блок')
    label = models.CharField(max_length=255, verbose_name='Текст кнопки')
    to = models.CharField(max_length=255, blank=True, verbose_name='Ссылка')
    trailing_icon = models.CharField(max_length=100, blank=True, verbose_name='Иконка (например i-lucide-arrow-right)')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Кнопка CTA'
        verbose_name_plural = 'Кнопки CTA'
        ordering = ['order']

    def __str__(self):
        return self.label


class LandingCTA(models.Model):
    """Блок «Начните экономить...» — призыв к действию."""
    title = models.CharField(max_length=500, verbose_name='Заголовок')
    description = models.TextField(blank=True, verbose_name='Описание')

    class Meta:
        verbose_name = 'Блок «Призыв к действию» (CTA)'
        verbose_name_plural = 'Блок «Призыв к действию» (CTA)'

    def __str__(self):
        return self.title[:50]
