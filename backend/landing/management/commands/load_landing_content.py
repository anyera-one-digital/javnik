"""
Загрузка начального контента лендинга в модели блоков.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from landing.models import (
    LandingHero,
    LandingFAQBlock,
    LandingFAQItem,
)


def load_from_yaml():
    """Загрузка из content/0.index.yml если есть."""
    base_dir = getattr(settings, 'BASE_DIR', None)
    for path in [
        os.path.join(base_dir, 'content', '0.index.yml') if base_dir else None,
        os.path.join(base_dir, '..', 'content', '0.index.yml') if base_dir else None,
    ]:
        if path and os.path.exists(path):
            try:
                import yaml
                with open(path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception:
                pass
    return None


class Command(BaseCommand):
    help = 'Загружает начальный контент лендинга (hero + FAQ)'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Перезаписать существующие данные')

    def handle(self, *args, **options):
        data = load_from_yaml()
        if not data:
            data = {
                'title': 'Онлайн-запись для частных специалистов. За 15 минут.',
                'description': 'Создайте своё расписание, добавьте услуги и получите личную ссылку для бронирования.',
                'seo': {'title': '', 'description': ''},
                'faq': {'title': '', 'description': '', 'items': []},
            }
            self.stdout.write(self.style.WARNING('Файл content/0.index.yml не найден, используются минимальные данные.'))

        force = options['force']

        if force or not LandingHero.objects.exists():
            LandingHero.objects.all().delete()
            LandingHero.objects.create(
                title=data.get('title', ''),
                description=data.get('description', ''),
                seo_title=data.get('seo', {}).get('title', ''),
                seo_description=data.get('seo', {}).get('description', ''),
            )
            self.stdout.write('  Hero: OK')

        if force or not LandingFAQBlock.objects.exists():
            LandingFAQBlock.objects.all().delete()
            faqb = data.get('faq', {})
            block = LandingFAQBlock.objects.create(
                title=faqb.get('title', ''),
                description=faqb.get('description', ''),
            )
            for j, item in enumerate(faqb.get('items', [])):
                LandingFAQItem.objects.create(
                    block=block,
                    label=item.get('label', ''),
                    content=item.get('content', ''),
                    order=j,
                )
            self.stdout.write('  FAQ: OK')

        self.stdout.write(self.style.SUCCESS('Контент лендинга загружен.'))
