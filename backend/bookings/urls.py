from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet,
    ServiceViewSet,
    MemberViewSet,
    EventViewSet,
    BookingViewSet,
    WorkScheduleViewSet,
    public_events_view,
    public_services_view,
    public_bookings_view,
    public_schedule_view,
    public_booking_create_view
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'members', MemberViewSet, basename='member')
router.register(r'events', EventViewSet, basename='event')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'schedule', WorkScheduleViewSet, basename='schedule')

urlpatterns = [
    path('', include(router.urls)),
]

# Публичные endpoints
public_urlpatterns = [
    path('public/events/<str:username>/', public_events_view, name='public_events'),
    path('public/services/<str:username>/', public_services_view, name='public_services'),
    path('public/bookings/<str:username>/', public_bookings_view, name='public_bookings'),
    path('public/schedule/<str:username>/', public_schedule_view, name='public_schedule'),
    path('public/bookings/<str:username>/create/', public_booking_create_view, name='public_booking_create'),
]
