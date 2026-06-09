"""
Сборка JSON-контента лендинга из моделей для API.
"""
from .models import LandingHero, LandingFAQBlock, LegalPage


def build_landing_content():
    """Собирает контент главной страницы: hero + FAQ."""
    content = {
        'title': '',
        'description': '',
        'seo': {'title': '', 'description': ''},
        'faq': None,
    }

    hero = LandingHero.objects.first()
    if hero:
        content['title'] = hero.title
        content['description'] = hero.description
        content['seo'] = {
            'title': hero.seo_title or hero.title,
            'description': hero.seo_description or hero.description,
        }

    faqb = LandingFAQBlock.objects.first()
    if faqb:
        content['faq'] = {
            'title': faqb.title,
            'description': faqb.description,
            'items': [
                {'label': i.label, 'content': i.content}
                for i in faqb.items.all()
            ],
        }

    return content


def build_legal_page_payload(page: LegalPage) -> dict:
    return {
        'slug': page.slug,
        'title': page.title,
        'subtitle': page.subtitle,
        'content': page.content,
        'seo': {
            'title': page.seo_title or page.title,
            'description': page.seo_description or '',
        },
        'updatedAt': page.updated_at.isoformat(),
    }
