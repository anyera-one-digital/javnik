"""
Клиент Т‑Кассы (интернет‑эквайринг T‑Bank).
Документация: https://developer.tbank.ru/eacq/api
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

EXCLUDE_TOKEN_KEYS = frozenset({'Token', 'Receipt', 'DATA', 'Shops'})


def is_tbank_configured() -> bool:
    key = str(getattr(settings, 'TBANK_TERMINAL_KEY', '') or '').strip()
    password = str(getattr(settings, 'TBANK_PASSWORD', '') or '').strip()
    return bool(key and password)


def _serialize_token_value(value: Any) -> str:
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return str(value)


def build_token(params: dict[str, Any], password: str) -> str:
    """Подпись запроса / уведомления по правилам T‑Bank."""
    token_params: dict[str, Any] = {
        k: v
        for k, v in params.items()
        if k not in EXCLUDE_TOKEN_KEYS and v is not None and v != ''
    }
    token_params['Password'] = password
    concatenated = ''.join(_serialize_token_value(token_params[k]) for k in sorted(token_params.keys()))
    return hashlib.sha256(concatenated.encode('utf-8')).hexdigest()


def verify_notification_token(payload: dict[str, Any], password: str) -> bool:
    received = payload.get('Token')
    if not received:
        return False
    expected = build_token(payload, password)
    return received == expected


def _ssl_verify() -> bool | str:
    """
    Проверка SSL к API Т‑Банка.
    На части VPS в цепочку вставляется свой CA → CERTIFICATE_VERIFY_FAILED.
    TBANK_SSL_VERIFY=false отключает проверку (только если иначе не заводится).
    TBANK_CA_BUNDLE=/path/to/ca.pem — свой CA.
    """
    bundle = str(getattr(settings, 'TBANK_CA_BUNDLE', '') or '').strip()
    if bundle:
        return bundle
    return bool(getattr(settings, 'TBANK_SSL_VERIFY', True))


def init_payment(
    *,
    order_id: str,
    amount: int,
    description: str,
    customer_key: str,
    success_url: str,
    fail_url: str,
    notification_url: str,
) -> dict[str, Any]:
    """POST /v2/Init — возвращает JSON ответа T‑Bank."""
    terminal_key = settings.TBANK_TERMINAL_KEY
    password = settings.TBANK_PASSWORD
    api_url = settings.TBANK_API_URL.rstrip('/')
    verify = _ssl_verify()
    if verify is False:
        logger.warning('T-Bank Init: SSL verification is DISABLED (TBANK_SSL_VERIFY=false)')

    payload: dict[str, Any] = {
        'TerminalKey': terminal_key,
        'Amount': amount,
        'OrderId': order_id,
        'Description': description[:140],
        'CustomerKey': customer_key[:36],
        'PayType': 'O',
        'Language': 'ru',
        'SuccessURL': success_url,
        'FailURL': fail_url,
        'NotificationURL': notification_url,
    }
    payload['Token'] = build_token(payload, password)

    try:
        response = requests.post(
            f'{api_url}/Init',
            json=payload,
            timeout=30,
            headers={'Content-Type': 'application/json'},
            verify=verify,
        )
        response.raise_for_status()
    except requests.exceptions.SSLError as exc:
        logger.exception('T-Bank Init SSL error')
        raise TBankAPIError(
            'SSL-ошибка при обращении к Т‑Банку. '
            'Проверьте CA на сервере или временно TBANK_SSL_VERIFY=false.',
            code='ssl_error',
        ) from exc
    except requests.exceptions.RequestException as exc:
        logger.exception('T-Bank Init network error')
        raise TBankAPIError(
            'Нет связи с платёжным сервисом Т‑Банка. Попробуйте позже.',
            code='network_error',
        ) from exc

    data = response.json()

    if not data.get('Success'):
        logger.warning('T-Bank Init failed: %s', data)
        raise TBankAPIError(
            data.get('Message') or data.get('Details') or 'Не удалось создать платёж',
            code=str(data.get('ErrorCode', '')),
        )

    return data


class TBankAPIError(Exception):
    def __init__(self, message: str, code: str = ''):
        super().__init__(message)
        self.code = code
