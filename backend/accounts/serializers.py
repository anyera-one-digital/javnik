from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User, Specialty


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации пользователя (шаг 1 — без username).
    Username заполняется на шаге 3 после подтверждения email.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    offer_accepted = serializers.BooleanField(required=True, write_only=True)
    privacy_accepted = serializers.BooleanField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ('email', 'phone', 'password', 'password_confirm', 'offer_accepted', 'privacy_accepted')
        extra_kwargs = {
            'email': {'required': True},
            'phone': {'required': True},
        }

    def validate_email(self, value):
        """Проверка уникальности email."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Пользователь с таким почтовым адресом уже существует.')
        return value

    def validate_phone(self, value):
        """Проверка уникальности номера телефона."""
        if not value or not value.strip():
            raise serializers.ValidationError('Укажите номер телефона.')
        normalized = value.strip()
        if User.objects.filter(phone=normalized).exists():
            raise serializers.ValidationError('Пользователь с таким номером телефона уже существует.')
        return normalized

    def validate_offer_accepted(self, value):
        if not value:
            raise serializers.ValidationError('Необходимо принять условия оферты.')
        return value

    def validate_privacy_accepted(self, value):
        if not value:
            raise serializers.ValidationError('Необходимо принять политику конфиденциальности.')
        return value

    def validate_username(self, value):
        """
        Валидация username для использования в поддомене
        """
        import re
        # Разрешаем только буквы, цифры, дефисы и подчеркивания
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                'Имя пользователя может содержать только буквы, цифры, дефисы и подчеркивания.'
            )
        # Минимум 3 символа
        if len(value) < 3:
            raise serializers.ValidationError('Имя пользователя должно содержать минимум 3 символа.')
        # Максимум 30 символов
        if len(value) > 30:
            raise serializers.ValidationError('Имя пользователя не должно превышать 30 символов.')
        # Не должно начинаться с дефиса или подчеркивания
        if value.startswith('-') or value.startswith('_'):
            raise serializers.ValidationError('Имя пользователя не должно начинаться с дефиса или подчеркивания.')
        return value.lower()  # Приводим к нижнему регистру

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Пароли не совпадают."
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        validated_data.pop('offer_accepted')
        validated_data.pop('privacy_accepted')
        import uuid
        validated_data.setdefault('username', f"u_{uuid.uuid4().hex[:12]}")
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения информации о пользователе
    """
    avatar_url = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    specialty = serializers.SerializerMethodField()
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        required=False,
        allow_null=True,
        source='specialty'
    )

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'avatar', 'avatar_url', 'display_name',
            'specialty', 'specialty_id', 'bio', 'city', 'service_address',
            'service_address_lat', 'service_address_lon',
            'is_email_verified', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'email', 'is_email_verified', 'created_at', 'updated_at', 'avatar_url', 'display_name', 'service_address_lat', 'service_address_lon', 'specialty')

    def get_specialty(self, obj):
        """Возвращает название специальности для отображения."""
        return obj.specialty.name if obj.specialty else None
    
    def validate_phone(self, value):
        """Проверка уникальности номера телефона при обновлении профиля."""
        if value and value.strip():
            normalized = value.strip()
            qs = User.objects.filter(phone=normalized)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError('Пользователь с таким номером телефона уже существует.')
            return normalized
        return value or None

    def validate_username(self, value):
        """
        Валидация username при обновлении
        """
        import re
        # Разрешаем только буквы, цифры, дефисы и подчеркивания
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                'Имя пользователя может содержать только буквы, цифры, дефисы и подчеркивания.'
            )
        # Минимум 3 символа
        if len(value) < 3:
            raise serializers.ValidationError('Имя пользователя должно содержать минимум 3 символа.')
        # Максимум 30 символов
        if len(value) > 30:
            raise serializers.ValidationError('Имя пользователя не должно превышать 30 символов.')
        # Не должно начинаться с дефиса или подчеркивания
        if value.startswith('-') or value.startswith('_'):
            raise serializers.ValidationError('Имя пользователя не должно начинаться с дефиса или подчеркивания.')
        return value.lower()  # Приводим к нижнему регистру
    
    def get_avatar_url(self, obj):
        """
        Возвращает полный URL аватара
        """
        if obj.avatar:
            request = self.context.get('request')
            if request:
                # Используем build_absolute_uri, но заменяем внутренний хост на доступный из браузера
                url = request.build_absolute_uri(obj.avatar.url)
                # Заменяем внутренние Docker имена хостов на localhost для разработки
                from django.conf import settings
                # Если URL содержит внутренний хост backend, заменяем на localhost
                if '://backend:' in url:
                    # Заменяем backend:8000 на localhost:8000
                    url = url.replace('://backend:8000', '://localhost:8000')
                elif '://backend/' in url:
                    # Заменяем backend/ на localhost:8000/
                    url = url.replace('://backend/', '://localhost:8000/')
                return url
            # Если нет request, возвращаем относительный путь
            return obj.avatar.url
        return None
    
    def get_display_name(self, obj):
        """
        Возвращает отображаемое имя (first_name или username)
        """
        if obj.first_name:
            return f"{obj.first_name} {obj.last_name or ''}".strip()
        return obj.username

    def update(self, instance, validated_data):
        """При обновлении адреса — геокодируем для Яндекс.Карт"""
        if 'service_address' in validated_data:
            addr = validated_data['service_address'] or ''
            if addr.strip():
                from .geocoding import geocode_address
                geo = geocode_address(addr.strip())
                validated_data['service_address_lat'] = geo['lat'] if geo else None
                validated_data['service_address_lon'] = geo['lon'] if geo else None
            else:
                validated_data['service_address_lat'] = None
                validated_data['service_address_lon'] = None
        return super().update(instance, validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Сериализатор для авторизации пользователя
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            if not user:
                raise serializers.ValidationError('Неверный email или пароль.')
            if not user.is_active:
                raise serializers.ValidationError('Аккаунт пользователя деактивирован.')
            if not getattr(user, 'is_email_verified', True):
                raise serializers.ValidationError('Подтвердите email. Проверьте почту и введите код из письма.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Необходимо указать email и пароль.')

        return attrs
