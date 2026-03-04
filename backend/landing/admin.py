"""
Админка для редактирования контента лендинга.
Каждый блок главной страницы — отдельный раздел с полями.
"""
from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (
    LandingImage,
    LandingHero,
    LandingSection,
    LandingSectionFeature,
    LandingFeatureBlock,
    LandingFeatureItem,
    LandingTestimonialBlock,
    LandingTestimonial,
    LandingPricingBlock,
    LandingPricingPlan,
    LandingPricingPlanFeature,
    LandingFAQBlock,
    LandingFAQItem,
    LandingCTA,
    LandingCTALink,
)


# === Inlines ===
class LandingSectionFeatureInline(admin.TabularInline):
    model = LandingSectionFeature
    extra = 1
    ordering = ['order']


class LandingFeatureItemInline(admin.TabularInline):
    model = LandingFeatureItem
    extra = 1
    ordering = ['order']


class LandingPricingPlanFeatureInline(admin.TabularInline):
    model = LandingPricingPlanFeature
    extra = 1
    ordering = ['order']


class LandingPricingPlanInline(admin.TabularInline):
    model = LandingPricingPlan
    extra = 0
    ordering = ['order']
    show_change_link = True


class LandingFAQItemInline(admin.TabularInline):
    model = LandingFAQItem
    extra = 1
    ordering = ['order']


class LandingCTALinkInline(admin.TabularInline):
    model = LandingCTALink
    extra = 1
    ordering = ['order']


# === Admin classes ===
@admin.register(LandingImage)
class LandingImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'alt_text', 'created_at', 'url_preview')
    list_filter = ('created_at',)
    search_fields = ('alt_text',)
    readonly_fields = ('created_at', 'url_preview')

    def url_preview(self, obj):
        if obj.image:
            url = obj.image.url
            return mark_safe(f'<code>{url}</code><br><img src="{url}" style="max-height: 100px; margin-top: 8px;">')
        return '—'
    url_preview.short_description = 'URL для вставки'


@admin.register(LandingHero)
class LandingHeroAdmin(admin.ModelAdmin):
    list_display = ('title',)
    fieldsets = (
        (None, {
            'fields': ('title', 'description'),
            'description': 'Главный экран — заголовок и описание на первом экране.',
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description'),
            'classes': ('collapse',),
        }),
    )


@admin.register(LandingSection)
class LandingSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'section_id')
    list_editable = ('order',)
    inlines = [LandingSectionFeatureInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'section_id', 'order'),
            'description': 'Блок секции (например «Для кого создан этот сервис» или «Вы больше никогда...»).',
        }),
        ('Изображение', {
            'fields': ('image', 'image_url'),
            'description': 'Загрузите изображение или укажите URL. Ниже — пункты секции.',
        }),
        ('Оформление', {
            'fields': ('orientation', 'reverse'),
        }),
    )


@admin.register(LandingFeatureBlock)
class LandingFeatureBlockAdmin(admin.ModelAdmin):
    list_display = ('title',)
    inlines = [LandingFeatureItemInline]
    fieldsets = (
        (None, {
            'fields': ('headline', 'title', 'description'),
            'description': 'Блок «Преимущества, которые вы оцените с первого дня».',
        }),
    )


@admin.register(LandingTestimonialBlock)
class LandingTestimonialBlockAdmin(admin.ModelAdmin):
    list_display = ('title',)
    fieldsets = (
        (None, {
            'fields': ('title', 'description'),
            'description': 'Заголовок и описание блока «Истории успеха». Отзывы редактируются отдельно.',
        }),
    )


@admin.register(LandingTestimonial)
class LandingTestimonialAdmin(admin.ModelAdmin):
    list_display = ('user_name', 'user_description', 'order', 'quote_preview')
    list_editable = ('order',)
    list_filter = ('order',)

    def quote_preview(self, obj):
        return obj.quote[:80] + '...' if len(obj.quote) > 80 else obj.quote
    quote_preview.short_description = 'Цитата'


@admin.register(LandingPricingBlock)
class LandingPricingBlockAdmin(admin.ModelAdmin):
    list_display = ('title',)
    inlines = [LandingPricingPlanInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'description'),
            'description': 'Блок «План для каждой потребности». Тарифы — ниже.',
        }),
    )


@admin.register(LandingPricingPlan)
class LandingPricingPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'block', 'price_month', 'price_year', 'highlight', 'order')
    list_editable = ('order',)
    inlines = [LandingPricingPlanFeatureInline]
    fieldsets = (
        (None, {
            'fields': ('block', 'title', 'description', 'order'),
        }),
        ('Цена', {
            'fields': ('price_month', 'price_year', 'button_label'),
        }),
        ('Оформление', {
            'fields': ('highlight', 'scale'),
        }),
    )


@admin.register(LandingFAQBlock)
class LandingFAQBlockAdmin(admin.ModelAdmin):
    list_display = ('title',)
    inlines = [LandingFAQItemInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'description'),
            'description': 'Блок «Часто задаваемые вопросы». Вопросы-ответы — ниже.',
        }),
    )


@admin.register(LandingCTA)
class LandingCTAAdmin(admin.ModelAdmin):
    list_display = ('title',)
    inlines = [LandingCTALinkInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'description'),
            'description': 'Блок «Начните экономить...» — призыв к действию с кнопками.',
        }),
    )
