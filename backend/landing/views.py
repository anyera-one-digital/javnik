"""
API для контента лендинга.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import LegalPage
from .serializers import build_landing_content, build_legal_page_payload


@api_view(['GET'])
@permission_classes([AllowAny])
def landing_page_detail(request, slug='index'):
    """
    Публичный endpoint для получения контента страницы лендинга.
    """
    if slug != 'index':
        return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    content = build_landing_content()
    return Response(content)


@api_view(['GET'])
@permission_classes([AllowAny])
def legal_page_detail(request, slug):
    """Публичный endpoint для юридических страниц (privacy, terms)."""
    try:
        page = LegalPage.objects.get(slug=slug)
    except LegalPage.DoesNotExist:
        return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response(build_legal_page_payload(page))
