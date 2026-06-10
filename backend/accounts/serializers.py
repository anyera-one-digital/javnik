from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User, Specialty
from .phone_validation import validate_ru_phone
from .subscription import build_subscription_payload, start_pro_trial
from bookings.effective_schedule import ALLOWED_SHIFT_CYCLES, ALLOWED_TEMPLATE_IDS


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Регистрация шаг 1: email, имя, согласия. Пароль задаётся после подтверждения почты.
    """
    offer_accepted = serializers.BooleanField(required=True, write_only=True)
    privacy_accepted = serializers.BooleanField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'offer_accepted', 'privacy_accepted')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
        }

    def validate_email(self, value):
        """Проверка уникальности email."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Пользователь с таким почтовым адресом уже существует.')
        return value

    def validate_first_name(self, value):
        if not value or not str(value).strip():
            raise serializers.ValidationError('Укажите имя.')
        return str(value).strip()

    def validate_offer_accepted(self, value):
        if not value:
            raise serializers.ValidationError('Необходимо принять условия пользования.')
        return value

    def validate_privacy_accepted(self, value):
        if not value:
            raise serializers.ValidationError('Необходимо принять политику конфиденциальности.')
        return value

    def create(self, validated_data):
        validated_data.pop('offer_accepted')
        validated_data.pop('privacy_accepted')
        import uuid
        user = User(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            username=f"u_{uuid.uuid4().hex[:12]}",
            phone=None,
        )
        user.set_unusable_password()
        user.save()
        start_pro_trial(user)
        return user


class RegisterCredentialsSerializer(serializers.Serializer):
    """Шаг после подтверждения email: только пароль."""
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

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user.is_authenticated and request.user.has_usable_password():
            raise serializers.ValidationError({'detail': 'Пароль уже установлен.'})
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Пароли не совпадают.'})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['password'])
        user.save()
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

    work_schedule_template = serializers.CharField(required=False, allow_blank=True, max_length=32)
    shift_cycle = serializers.CharField(required=False, allow_blank=True, max_length=8)
    shift_anchor_date = serializers.DateField(required=False, allow_null=True)
    subscription = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'avatar', 'avatar_url', 'display_name',
            'specialty', 'specialty_id', 'bio', 'city', 'service_address',
            'service_address_lat', 'service_address_lon',
            'is_email_verified', 'show_public_schedule', 'show_public_reviews',
            'show_public_portfolio', 'created_at', 'updated_at',
            'work_schedule_template', 'shift_cycle', 'shift_anchor_date',
            'subscription',
        )
        read_only_fields = (
            'id', 'email', 'is_email_verified', 'created_at', 'updated_at',
            'avatar_url', 'display_name', 'service_address_lat', 'service_address_lon',
            'specialty', 'subscription',
        )

    def get_subscription(self, obj):
        return build_subscription_payload(obj)

    def get_specialty(self, obj):
        """Возвращает название специальности для отображения."""
        return obj.specialty.name if obj.specialty else None
    
    def validate_phone(self, value):
        """Формат +7 / РФ и уникальность при обновлении профиля."""
        if not value or not str(value).strip():
            return None
        value = validate_ru_phone(str(value).strip(), required=True)
        qs = User.objects.filter(phone=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Пользователь с таким номером телефона уже существует.')
        return value

    def validate_work_schedule_template(self, value):
        if not value or not str(value).strip():
            return 'standard-5'
        v = str(value).strip()
        if v not in ALLOWED_TEMPLATE_IDS:
            raise serializers.ValidationError('Неизвестный шаблон графика.')
        return v

    def validate_shift_cycle(self, value):
        if value is None or (isinstance(value, str) and not str(value).strip()):
            return '2-2'
        v = str(value).strip()
        if v not in ALLOWED_SHIFT_CYCLES:
            raise serializers.ValidationError('Недопустимый цикл смены.')
        return v

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
        """Относительный URL аватара — браузер подставит текущий origin (https://javnik.ru)."""
        if obj.avatar:
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


class DeleteAccountSerializer(serializers.Serializer):
    """Подтверждение удаления аккаунта вводом username."""

    username = serializers.CharField(required=True, max_length=150)

    def validate_username(self, value):
        user = self.context['request'].user
        if value != user.username:
            raise serializers.ValidationError(
                'Имя пользователя не совпадает. Введите его точно, как в профиле.'
            )
        return value
