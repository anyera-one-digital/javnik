"""
Админка для редактирования контента лендинга.
"""
from django import forms
from django.contrib import admin
from .models import (
    LandingHero,
    LandingFAQBlock,
    LandingFAQItem,
    LegalPage,
)


class LandingFAQItemInline(admin.TabularInline):
    model = LandingFAQItem
    extra = 1
    ordering = ['order']


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


class LegalPageAdminForm(forms.ModelForm):
    class Meta:
        model = LegalPage
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={'rows': 40, 'cols': 120}),
            'seo_description': forms.Textarea(attrs={'rows': 3}),
        }


@admin.register(LegalPage)
class LegalPageAdmin(admin.ModelAdmin):
    form = LegalPageAdminForm
    list_display = ('slug', 'title', 'updated_at')
    readonly_fields = ('slug', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('slug', 'title', 'subtitle', 'content'),
            'description': (
                'Редактируйте текст страницы в формате HTML. '
                'Изменения сразу отображаются на сайте по адресам /privacy и /terms.'
            ),
        }),
        ('SEO', {
            'fields': ('seo_title', 'seo_description'),
            'classes': ('collapse',),
        }),
        ('Служебное', {
            'fields': ('updated_at',),
        }),
    )
