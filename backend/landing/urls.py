from django.urls import path
from . import views

urlpatterns = [
    path('landing/', views.landing_page_detail),
    path('landing/<slug:slug>/', views.landing_page_detail),
]
