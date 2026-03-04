from django.urls import path
from .views import (
    public_events_view,
    public_services_view,
    public_bookings_view,
    public_schedule_view,
    public_booking_create_view,
    public_reviews_view
)

app_name = 'bookings_public'

urlpatterns = [
    path('public/events/<str:username>/', public_events_view, name='public_events'),
    path('public/services/<str:username>/', public_services_view, name='public_services'),
    path('public/bookings/<str:username>/', public_bookings_view, name='public_bookings'),
    path('public/schedule/<str:username>/', public_schedule_view, name='public_schedule'),
    path('public/bookings/<str:username>/create/', public_booking_create_view, name='public_booking_create'),
    path('public/reviews/<str:username>/', public_reviews_view, name='public_reviews'),
]
