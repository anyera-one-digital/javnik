from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerViewSet,
    ServiceViewSet,
    EventViewSet,
    BookingViewSet,
    WorkScheduleViewSet,
    analytics_stats_view,
    analytics_revenue_view,
    analytics_services_breakdown_view,
)

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'events', EventViewSet, basename='event')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'schedule', WorkScheduleViewSet, basename='schedule')

urlpatterns = [
    path('', include(router.urls)),
    path('analytics/stats/', analytics_stats_view, name='analytics_stats'),
    path('analytics/revenue/', analytics_revenue_view, name='analytics_revenue'),
    path(
        'analytics/services-breakdown/',
        analytics_services_breakdown_view,
        name='analytics_services_breakdown',
    ),
]
