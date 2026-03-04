"""
URL configuration for bookly_api project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_root(request):
    """Корневой endpoint API"""
    return JsonResponse({
        'message': 'Bookly API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth/',
            'admin': '/admin/',
        }
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/', include('bookings.urls')),
    path('api/public/', include('accounts.public_urls')),  # Публичные endpoints профилей
    path('api/', include('bookings.public_urls')),  # Публичные endpoints событий и услуг
    path('api/', include('landing.urls')),  # Контент лендинга
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
