from django.urls import path
from . import views

app_name = 'accounts_public'

urlpatterns = [
    path('profile/<str:username>/', views.public_profile_view, name='public_profile'),
    path('specialties/', views.specialties_list_view, name='specialties_list'),
]
