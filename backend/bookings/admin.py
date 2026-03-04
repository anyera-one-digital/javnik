from django.contrib import admin
from .models import Customer, Service, ServiceImage, Member, Event, Booking, WorkSchedule, WorkBreak, Review


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'status', 'user', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 0
    fields = ('image', 'order')
    readonly_fields = ('created_at',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'duration', 'price', 'active', 'user', 'created_at')
    list_filter = ('active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ServiceImageInline]


@admin.register(ServiceImage)
class ServiceImageAdmin(admin.ModelAdmin):
    list_display = ('service', 'order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('service__name',)
    readonly_fields = ('created_at',)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'position', 'active', 'user', 'created_at')
    list_filter = ('active', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'start_time', 'service', 'member', 'max_participants', 'booked_slots', 'user')
    list_filter = ('date', 'service', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer', 'service', 'date', 'start_time', 'status', 'member', 'user', 'created_at')
    list_filter = ('status', 'date', 'created_at')
    search_fields = ('customer__name', 'service__name', 'notes')
    readonly_fields = ('created_at', 'updated_at')


class WorkBreakInline(admin.TabularInline):
    model = WorkBreak
    extra = 0
    fields = ('start_time', 'end_time')


@admin.register(WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'type', 'start_time', 'end_time')
    list_filter = ('type', 'date')
    search_fields = ('user__username', 'user__email')
    inlines = [WorkBreakInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'user', 'service', 'rating', 'created_at')
    list_filter = ('rating', 'created_at', 'service')
    search_fields = ('customer_name', 'comment', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'customer', 'customer_name', 'service', 'rating')
        }),
        ('Отзыв', {
            'fields': ('comment', 'photos')
        }),
        ('Ответ специалиста', {
            'fields': ('reply', 'reply_author'),
            'classes': ('collapse',)
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
