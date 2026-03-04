"""
Интеграция с Yandex Geosuggest, DaData и Geocoder API для подсказок адресов.
Результаты совместимы с отображением на Яндекс.Картах.
"""
import logging
import urllib.parse
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _suggest_yandex(query: str, limit: int) -> list[dict]:
    """Yandex Geosuggest API."""
    api_key = getattr(settings, 'YANDEX_MAPS_API_KEY', None)
    if not api_key:
        return []

    params = {
        'apikey': api_key,
        'text': query.strip(),
        'lang': 'ru_RU',
        'results': min(limit, 10),
        'attrs': 'uri',
        'print_address': 1,
    }
    url = 'https://suggest-maps.yandex.ru/v1/suggest?' + urllib.parse.urlencode(params)
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning('Yandex Geosuggest request failed: %s', e)
        return []

    results = []
    for item in data.get('results', [])[:limit]:
        title = item.get('title', {}).get('text', '')
        addr = item.get('address', {})
        full_address = addr.get('formatted_address') or title if isinstance(addr, dict) else title
        results.append({'address': full_address or title, 'title': title, 'uri': item.get('uri')})
    return results


def _suggest_dadata(query: str, limit: int) -> list[dict]:
    """DaData API (бесплатный тариф ~10k запросов/день)."""
    api_key = getattr(settings, 'DADATA_API_KEY', None)
    if not api_key:
        return []

    url = 'https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Token {api_key}',
    }
    payload = {'query': query.strip(), 'count': min(limit, 10)}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning('DaData suggest request failed: %s', e)
        return []

    results = []
    for item in data.get('suggestions', [])[:limit]:
        value = item.get('value') or item.get('unrestricted_value', '')
        if value:
            results.append({'address': value, 'title': value, 'uri': None})
    return results


def suggest_addresses(query: str, limit: int = 7) -> list[dict]:
    """
    Получить подсказки адресов. Сначала Yandex, при отсутствии ключа — DaData.
    Возвращает: [{"address": str, "title": str, "uri": str | None}, ...]
    """
    if not query or len(query.strip()) < 2:
        return []

    results = _suggest_yandex(query, limit)
    if not results:
        results = _suggest_dadata(query, limit)
    return results


def geocode_address(address: str) -> Optional[dict]:
    """
    Получить координаты через Yandex Geocoder API.
    address: полный адрес или uri из Geosuggest.
    Возвращает {"lat": float, "lon": float, "address": str} или None.
    """
    api_key = getattr(settings, 'YANDEX_MAPS_API_KEY', None)
    if not api_key or not address:
        return None

    params = {
        'apikey': api_key,
        'geocode': address,
        'format': 'json',
        'lang': 'ru_RU',
    }
    url = 'https://geocode-maps.yandex.ru/1.x/?' + urllib.parse.urlencode(params)

    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.warning('Yandex Geocoder request failed: %s', e)
        return None

    try:
        geo = data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember', [])
        if not geo:
            return None
        obj = geo[0].get('GeoObject', {})
        pos = obj.get('Point', {}).get('pos', '').split()
        if len(pos) != 2:
            return None
        lon, lat = float(pos[0]), float(pos[1])
        meta = obj.get('metaDataProperty', {}).get('GeocoderMetaData', {})
        address = meta.get('text', '')
        return {'lat': lat, 'lon': lon, 'address': address}
    except (KeyError, ValueError, IndexError):
        return None
