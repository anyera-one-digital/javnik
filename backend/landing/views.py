"""
API для контента лендинга.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .serializers import build_landing_content


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
