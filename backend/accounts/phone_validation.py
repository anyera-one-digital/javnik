import re

from rest_framework import serializers

PHONE_ERROR = 'Введите корректный номер телефона'


def _digits(value: str) -> str:
    return re.sub(r'\D', '', value or '')


def validate_ru_phone(value: str, *, required: bool = True) -> str:
    """Проверка формата РФ (+7 / 10 цифр с 9)."""
    s = (value or '').strip()
    if not s:
        if required:
            raise serializers.ValidationError('Укажите номер телефона.')
        return ''
    d = _digits(s)
    if len(d) < 10 or len(d) > 11:
        raise serializers.ValidationError(PHONE_ERROR)
    if len(d) == 11:
        if d[0] not in ('7', '8'):
            raise serializers.ValidationError(PHONE_ERROR)
    else:
        if d[0] != '9':
            raise serializers.ValidationError(PHONE_ERROR)
    return s.strip()
