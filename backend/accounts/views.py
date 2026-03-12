import hashlib
import logging

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.crypto import get_random_string
from django.conf import settings

from bookings.tasks import send_email_verification_code
from .models import SpecialtyCategory
from .serializers import UserRegistrationSerializer, UserSerializer, LoginSerializer

logger = logging.getLogger(__name__)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    Регистрация нового пользователя (шаг 1).
    Создаёт пользователя с is_email_verified=False, отправляет код на email.
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user.is_email_verified = False
        user.save()

        email = user.email
        code = get_random_string(length=6, allowed_chars='0123456789')
        cache_key = f'email_verify_{hashlib.sha256(email.encode()).hexdigest()}'
        cache.set(cache_key, {'code': code, 'email': email, 'user_id': user.id}, timeout=900)

        try:
            send_email_verification_code.delay(user_id=user.id, code=code)
        except Exception as e:
            logger.error(f'Ошибка отправки задачи Celery: {e}')
            if settings.DEBUG:
                return Response({
                    'message': 'Код отправлен на почту.',
                    'email': email,
                    'needs_verification': True,
                    'debug_code': code,
                }, status=status.HTTP_201_CREATED)
            raise

        return Response({
            'message': 'Код подтверждения отправлен на почту.',
            'email': email,
            'needs_verification': True,
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_email_view(request):
    """
    Подтверждение email (шаг 2 регистрации).
    POST /api/auth/verify-email/
    Body: { "email": "user@example.com", "code": "123456" }

    В режиме DEBUG: если задан EMAIL_VERIFY_ADMIN_CODE в .env, код с этим значением
    подтверждает любой email без проверки кэша (для разработки).
    """
    email = (request.data.get('email') or '').strip()
    code = str(request.data.get('code') or '').strip()

    if not email or not code:
        return Response({
            'error': 'Укажите email и код подтверждения.',
        }, status=status.HTTP_400_BAD_REQUEST)

    # Админский обход: только при DEBUG и заданном EMAIL_VERIFY_ADMIN_CODE
    admin_code = getattr(settings, 'EMAIL_VERIFY_ADMIN_CODE', None)
    if settings.DEBUG and admin_code and code == str(admin_code).strip():
        try:
            user = User.objects.get(email__iexact=email, is_email_verified=False)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь с таким email не найден или уже подтверждён.'}, status=status.HTTP_404_NOT_FOUND)
        user.is_email_verified = True
        user.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Регистрация завершена.',
        }, status=status.HTTP_200_OK)

    cache_key = f'email_verify_{hashlib.sha256(email.encode()).hexdigest()}'
    cached = cache.get(cache_key)

    if not cached:
        return Response({
            'error': 'Код истёк или недействителен. Запросите новый код.',
        }, status=status.HTTP_400_BAD_REQUEST)

    if cached['code'] != code or cached['email'] != email:
        return Response({
            'error': 'Неверный код подтверждения.',
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=cached['user_id'], email=email)
    except User.DoesNotExist:
        return Response({'error': 'Пользователь не найден.'}, status=status.HTTP_404_NOT_FOUND)

    user.is_email_verified = True
    user.save()
    cache.delete(cache_key)

    refresh = RefreshToken.for_user(user)
    return Response({
        'user': UserSerializer(user, context={'request': request}).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
        'message': 'Регистрация завершена.',
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_verification_code_view(request):
    """
    Повторная отправка кода подтверждения.
    POST /api/auth/resend-verification/
    Body: { "email": "user@example.com" }
    """
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Укажите email.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email, is_email_verified=False)
    except User.DoesNotExist:
        return Response({
            'message': 'Если пользователь с таким email существует и не подтверждён, код отправлен.',
        }, status=status.HTTP_200_OK)

    code = get_random_string(length=6, allowed_chars='0123456789')
    cache_key = f'email_verify_{hashlib.sha256(email.encode()).hexdigest()}'
    cache.set(cache_key, {'code': code, 'email': email, 'user_id': user.id}, timeout=900)

    try:
        send_email_verification_code.delay(user_id=user.id, code=code)
    except Exception as e:
        logger.error(f'Ошибка отправки задачи Celery: {e}')
        if settings.DEBUG:
            return Response({'message': 'Код отправлен.', 'debug_code': code}, status=status.HTTP_200_OK)
        return Response({'error': 'Ошибка отправки. Попробуйте позже.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({'message': 'Код отправлен на почту.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    Авторизация пользователя
    POST /api/auth/login/
    Если пользователь не подтвердил email — возвращает needs_verification.
    """
    from django.contrib.auth import authenticate

    email = request.data.get('email')
    password = request.data.get('password')
    if email and password:
        user = authenticate(request=request, username=email, password=password)
        if user and not user.is_active:
            return Response({'detail': 'Аккаунт пользователя деактивирован.'}, status=status.HTTP_400_BAD_REQUEST)
        if user and not getattr(user, 'is_email_verified', True):
            return Response({
                'needs_verification': True,
                'email': user.email,
                'message': 'Подтвердите email. Введите код из письма.',
            }, status=status.HTTP_200_OK)

    serializer = LoginSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']

    refresh = RefreshToken.for_user(user)
    return Response({
        'user': UserSerializer(user, context={'request': request}).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
        'message': 'Успешный вход в систему.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Выход пользователя (отзыв токена)
    POST /api/auth/logout/
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({
            'message': 'Успешный выход из системы.'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Неверный токен.',
            'detail': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_view(request):
    """
    Получение профиля текущего пользователя
    GET /api/auth/profile/
    """
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_profile_view(request):
    """
    Обновление профиля пользователя
    PUT/PATCH /api/auth/profile/
    """
    serializer = UserSerializer(request.user, data=request.data, partial=True, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response({
        'user': serializer.data,
        'message': 'Профиль успешно обновлен.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_avatar_view(request):
    """
    Загрузка аватара пользователя
    POST /api/auth/avatar/
    """
    if 'avatar' not in request.FILES:
        return Response({
            'error': 'Файл аватара не предоставлен.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    avatar_file = request.FILES['avatar']
    
    # Валидация размера файла (максимум 1 МБ)
    if avatar_file.size > 1024 * 1024:
        return Response({
            'error': 'Размер файла превышает 1 МБ.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Валидация типа файла
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
    if avatar_file.content_type not in allowed_types:
        return Response({
            'error': 'Недопустимый тип файла. Разрешены только JPG, PNG и GIF.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Сохранение аватара
    user = request.user
    user.avatar = avatar_file
    user.save()
    
    serializer = UserSerializer(user, context={'request': request})
    return Response({
        'user': serializer.data,
        'message': 'Аватар успешно загружен.'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def specialties_list_view(request):
    """
    Список специальностей с группировкой по категориям.
    GET /api/public/specialties/
    """
    categories = SpecialtyCategory.objects.prefetch_related('specialties').order_by('order', 'name')
    data = [
        {
            'id': cat.id,
            'name': cat.name,
            'order': cat.order,
            'specialties': [
                {'id': s.id, 'name': s.name, 'order': s.order}
                for s in cat.specialties.order_by('order', 'name')
            ],
        }
        for cat in categories
    ]
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_profile_view(request, username):
    """
    Получение публичного профиля пользователя по username
    GET /api/public/profile/<username>/
    """
    try:
        user = User.objects.get(username=username, is_active=True)
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'error': 'Пользователь не найден.'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def address_suggest_view(request):
    """
    Подсказки адресов через Yandex Geosuggest.
    GET /api/auth/address-suggest/?q=Георгия Димитрова
    """
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return Response({'results': []}, status=status.HTTP_200_OK)

    from .geocoding import suggest_addresses
    results = suggest_addresses(q, limit=7)
    return Response({'results': results}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_view(request):
    """
    Отправка кода подтверждения для восстановления пароля
    POST /api/auth/password-reset/
    Body: { "email": "user@example.com" }
    """
    email = request.data.get('email')
    
    if not email:
        return Response({
            'error': 'Email обязателен для заполнения.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        # Не раскрываем информацию о том, существует ли пользователь
        return Response({
            'message': 'Если пользователь с таким email существует, код подтверждения отправлен на почту.'
        }, status=status.HTTP_200_OK)
    
    # Генерируем 6-значный код
    code = get_random_string(length=6, allowed_chars='0123456789')

    # Сохраняем код в кэше на 15 минут
    # Используем хеш email для безопасности
    cache_key = f'password_reset_{hashlib.sha256(email.encode()).hexdigest()}'
    cache.set(cache_key, {
        'code': code,
        'email': email,
        'user_id': user.id
    }, timeout=900)  # 15 минут

    try:
        send_email_verification_code.delay(user_id=user.id, code=code)
    except Exception as e:
        logger.error(f'Ошибка отправки задачи Celery: {e}')
        if settings.DEBUG:
            return Response({
                'message': 'Код подтверждения отправлен на почту.',
                'debug_code': code  # Только в режиме отладки
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Ошибка при отправке email. Попробуйте позже.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'message': 'Код подтверждения отправлен на почту.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm_view(request):
    """
    Подтверждение кода и установка нового пароля
    POST /api/auth/password-reset/confirm/
    Body: { "email": "user@example.com", "code": "123456", "new_password": "newpass123" }
    """
    email = request.data.get('email')
    code = request.data.get('code')
    new_password = request.data.get('new_password')
    
    if not all([email, code, new_password]):
        return Response({
            'error': 'Необходимо указать email, код и новый пароль.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Проверяем длину пароля
    if len(new_password) < 8:
        return Response({
            'error': 'Пароль должен содержать минимум 8 символов.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Получаем данные из кэша
    cache_key = f'password_reset_{hashlib.sha256(email.encode()).hexdigest()}'
    cached_data = cache.get(cache_key)
    
    if not cached_data:
        return Response({
            'error': 'Код истек или недействителен. Запросите новый код.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Проверяем код
    if cached_data['code'] != code:
        return Response({
            'error': 'Неверный код подтверждения.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Проверяем email
    if cached_data['email'] != email:
        return Response({
            'error': 'Email не совпадает.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=cached_data['user_id'], email=email, is_active=True)
    except User.DoesNotExist:
        return Response({
            'error': 'Пользователь не найден.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Устанавливаем новый пароль
    user.set_password(new_password)
    user.save()
    
    # Удаляем код из кэша
    cache.delete(cache_key)
    
    return Response({
        'message': 'Пароль успешно изменен.'
    }, status=status.HTTP_200_OK)
