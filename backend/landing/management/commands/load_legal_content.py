"""
Загрузка начального контента юридических страниц (privacy, terms).
"""
import os
from django.core.management.base import BaseCommand
from landing.models import LegalPage


DEFAULT_PAGES = {
    LegalPage.SLUG_PRIVACY: {
        'title': 'Политика в отношении обработки персональных данных',
        'subtitle': '',
        'seo_title': 'Политика конфиденциальности',
        'seo_description': 'Политика в отношении обработки персональных данных ООО «ЭНИЕРА»',
    },
    LegalPage.SLUG_TERMS: {
        'title': 'Пользовательское соглашение',
        'subtitle': 'в отношении сервиса онлайн-записи «Явьник»',
        'seo_title': 'Пользовательское соглашение',
        'seo_description': 'Пользовательское соглашение сервиса онлайн-записи «Явьник» (ООО «ЭНИЕРА»)',
    },
}


def data_dir():
    return os.path.join(os.path.dirname(__file__), '..', '..', 'data')


def read_html(slug: str) -> str:
    path = os.path.join(data_dir(), f'{slug}.html')
    with open(path, encoding='utf-8') as f:
        return f.read()


class Command(BaseCommand):
    help = 'Загружает начальный контент юридических страниц (privacy, terms)'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Перезаписать существующие данные')

    def handle(self, *args, **options):
        force = options['force']

        for slug, meta in DEFAULT_PAGES.items():
            if not force and LegalPage.objects.filter(slug=slug).exists():
                self.stdout.write(f'  {slug}: пропуск (уже существует, используйте --force)')
                continue

            content = read_html(slug)
            LegalPage.objects.update_or_create(
                slug=slug,
                defaults={
                    'title': meta['title'],
                    'subtitle': meta['subtitle'],
                    'content': content,
                    'seo_title': meta['seo_title'],
                    'seo_description': meta['seo_description'],
                },
            )
            self.stdout.write(f'  {slug}: OK')

        self.stdout.write(self.style.SUCCESS('Юридические страницы загружены.'))
