"""
Загрузка начального контента лендинга в модели блоков.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from landing.models import (
    LandingHero,
    LandingSection,
    LandingSectionFeature,
    LandingFeatureBlock,
    LandingFeatureItem,
    LandingTestimonialBlock,
    LandingTestimonial,
    LandingPricingBlock,
    LandingPricingPlan,
    LandingPricingPlanFeature,
    LandingFAQBlock,
    LandingFAQItem,
    LandingCTA,
    LandingCTALink,
)


def load_from_yaml():
    """Загрузка из content/0.index.yml если есть."""
    base_dir = getattr(settings, 'BASE_DIR', None)
    for path in [
        os.path.join(base_dir, 'content', '0.index.yml') if base_dir else None,  # Docker: content смонтирован в /app/content
        os.path.join(base_dir, '..', 'content', '0.index.yml') if base_dir else None,  # Локально: content рядом с backend
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
    help = 'Загружает начальный контент лендинга в блоки'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Перезаписать существующие данные')

    def handle(self, *args, **options):
        data = load_from_yaml()
        if not data:
            # Fallback: встроенные данные
            data = {
                'title': 'Онлайн-запись для частных специалистов. За 15 минут.',
                'description': 'Создайте своё расписание, добавьте услуги и получите личную ссылку для бронирования.',
                'seo': {'title': '', 'description': ''},
                'sections': [],
                'features': {'headline': '', 'title': '', 'description': '', 'items': []},
                'testimonials': {'title': '', 'description': '', 'items': []},
                'pricing': {'title': '', 'description': '', 'plans': []},
                'faq': {'title': '', 'description': '', 'items': []},
                'cta': {'title': '', 'description': '', 'links': []},
            }
            self.stdout.write(self.style.WARNING('Файл content/0.index.yml не найден, используются минимальные данные.'))

        force = options['force']

        # Hero
        if force or not LandingHero.objects.exists():
            LandingHero.objects.all().delete()
            LandingHero.objects.create(
                title=data.get('title', ''),
                description=data.get('description', ''),
                seo_title=data.get('seo', {}).get('title', ''),
                seo_description=data.get('seo', {}).get('description', ''),
            )
            self.stdout.write('  Hero: OK')

        # Sections
        if force or not LandingSection.objects.exists():
            LandingSection.objects.all().delete()
            for i, s in enumerate(data.get('sections', [])):
                sec = LandingSection.objects.create(
                    title=s.get('title', ''),
                    description=s.get('description', ''),
                    section_id=s.get('id', ''),
                    image_url=s.get('image', '') if isinstance(s.get('image'), str) else '',
                    orientation=s.get('orientation', 'horizontal'),
                    reverse=s.get('reverse', False),
                    order=i,
                )
                for j, f in enumerate(s.get('features', [])):
                    LandingSectionFeature.objects.create(
                        section=sec,
                        name=f.get('name', ''),
                        description=f.get('description', ''),
                        icon=f.get('icon', 'i-lucide-circle'),
                        order=j,
                    )
            self.stdout.write('  Sections: OK')

        # Features block
        if force or not LandingFeatureBlock.objects.exists():
            LandingFeatureBlock.objects.all().delete()
            fb = data.get('features', {})
            block = LandingFeatureBlock.objects.create(
                headline=fb.get('headline', ''),
                title=fb.get('title', ''),
                description=fb.get('description', ''),
            )
            for j, item in enumerate(fb.get('items', [])):
                LandingFeatureItem.objects.create(
                    block=block,
                    title=item.get('title', ''),
                    description=item.get('description', ''),
                    icon=item.get('icon', 'i-lucide-circle'),
                    order=j,
                )
            self.stdout.write('  Features: OK')

        # Testimonials
        if force or not LandingTestimonialBlock.objects.exists():
            LandingTestimonialBlock.objects.all().delete()
            LandingTestimonial.objects.all().delete()
            tb = data.get('testimonials', {})
            LandingTestimonialBlock.objects.create(
                title=tb.get('title', ''),
                description=tb.get('description', ''),
            )
            for j, t in enumerate(tb.get('items', [])):
                user = t.get('user', {})
                avatar = user.get('avatar') or {}
                src = avatar.get('src', '') if isinstance(avatar, dict) else ''
                LandingTestimonial.objects.create(
                    quote=t.get('quote', ''),
                    user_name=user.get('name', ''),
                    user_description=user.get('description', ''),
                    user_avatar_url=src,
                    order=j,
                )
            self.stdout.write('  Testimonials: OK')

        # Pricing
        if force or not LandingPricingBlock.objects.exists():
            LandingPricingPlanFeature.objects.all().delete()
            LandingPricingPlan.objects.all().delete()
            LandingPricingBlock.objects.all().delete()
            pb = data.get('pricing', {})
            block = LandingPricingBlock.objects.create(
                title=pb.get('title', ''),
                description=pb.get('description', ''),
            )
            for j, p in enumerate(pb.get('plans', [])):
                price = p.get('price', {})
                btn = p.get('button', {})
                plan = LandingPricingPlan.objects.create(
                    block=block,
                    title=p.get('title', ''),
                    description=p.get('description', ''),
                    price_month=price.get('month', ''),
                    price_year=price.get('year', ''),
                    button_label=btn.get('label', 'Начать'),
                    highlight=p.get('highlight', False),
                    scale=p.get('scale', False),
                    order=j,
                )
                for k, feat in enumerate(p.get('features', [])):
                    LandingPricingPlanFeature.objects.create(plan=plan, text=feat, order=k)
            self.stdout.write('  Pricing: OK')

        # FAQ
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

        # CTA
        if force or not LandingCTA.objects.exists():
            LandingCTA.objects.all().delete()
            cta = data.get('cta', {})
            block = LandingCTA.objects.create(
                title=cta.get('title', ''),
                description=cta.get('description', ''),
            )
            for j, link in enumerate(cta.get('links', [])):
                LandingCTALink.objects.create(
                    block=block,
                    label=link.get('label', ''),
                    to=link.get('to', ''),
                    trailing_icon=link.get('trailingIcon', ''),
                    order=j,
                )
            self.stdout.write('  CTA: OK')

        self.stdout.write(self.style.SUCCESS('Контент лендинга загружен.'))
