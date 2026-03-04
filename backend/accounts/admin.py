from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SpecialtyCategory, Specialty


class SpecialtyInline(admin.TabularInline):
    model = Specialty
    extra = 1
    ordering = ['order', 'name']


@admin.register(SpecialtyCategory)
class SpecialtyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'specialties_count')
    ordering = ['order', 'name']
    inlines = [SpecialtyInline]

    def specialties_count(self, obj):
        return obj.specialties.count()
    specialties_count.short_description = 'Специальностей'


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'order')
    list_filter = ('category',)
    ordering = ['category', 'order', 'name']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'phone', 'city', 'is_staff', 'is_active', 'is_email_verified', 'created_at')
    list_filter = ('is_staff', 'is_active', 'is_email_verified', 'created_at')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone', 'city', 'service_address')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')
    
    fieldsets = (
        (None, {
            'fields': ('username', 'email', 'password')
        }),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'phone', 'avatar')
        }),
        ('Профиль (данные из личного кабинета)', {
            'fields': ('specialty', 'bio', 'city', 'service_address', 'service_address_lat', 'service_address_lon'),
            'description': 'Поля, заполняемые пользователем в личном кабинете. Можно редактировать вручную в обход фронтенда.'
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Важные даты', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
        ('Дополнительная информация', {
            'fields': ('is_email_verified',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone'),
        }),
    )
