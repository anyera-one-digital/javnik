from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import SubscriptionPayment, User, SpecialtyCategory, Specialty
from .subscription import get_effective_plan, PLAN_LABELS


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


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'amount', 'billing_period', 'status', 'created_at', 'paid_at')
    list_filter = ('status', 'billing_period', 'created_at')
    search_fields = ('order_id', 'payment_id', 'user__email', 'user__username')
    readonly_fields = ('order_id', 'payment_id', 'payment_url', 'created_at', 'paid_at')
    ordering = ('-created_at',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', 'username', 'first_name', 'subscription_plan',
        'subscription_effective_display', 'subscription_expires_at',
        'is_staff', 'is_active', 'created_at',
    )
    list_filter = ('subscription_plan', 'is_staff', 'is_active', 'is_email_verified', 'created_at')
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
        ('Подписка', {
            'fields': (
                'subscription_plan',
                'subscription_expires_at',
                'subscription_started_at',
                'subscription_granted_via',
            ),
            'description': (
                'Pro без даты окончания — бессрочный. Для Free оставьте дату пустой. '
                '«Источник» при ручной выдаче укажите «Вручную (админка)».'
            ),
        }),
        ('Дополнительная информация', {
            'fields': ('is_email_verified',)
        }),
    )

    @admin.display(description='Активный тариф')
    def subscription_effective_display(self, obj):
        return PLAN_LABELS.get(get_effective_plan(obj), get_effective_plan(obj))
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'phone'),
        }),
    )
