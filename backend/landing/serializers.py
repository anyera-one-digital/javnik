"""
Сборка JSON-контента лендинга из моделей для API.
"""
from .models import (
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


def build_landing_content():
    """Собирает контент главной страницы из моделей."""
    content = {
        'title': '',
        'description': '',
        'seo': {'title': '', 'description': ''},
        'sections': [],
        'features': None,
        'testimonials': None,
        'pricing': None,
        'faq': None,
        'cta': None,
    }

    # Hero
    hero = LandingHero.objects.first()
    if hero:
        content['title'] = hero.title
        content['description'] = hero.description
        content['seo'] = {
            'title': hero.seo_title or hero.title,
            'description': hero.seo_description or hero.description,
        }

    # Sections
    for s in LandingSection.objects.all():
        section_data = {
            'title': s.title,
            'description': s.description,
            'id': s.section_id or '',
            'orientation': s.orientation,
            'reverse': s.reverse,
            'image': s.get_image_url(),
            'features': [],
        }
        for f in s.features.all():
            section_data['features'].append({
                'name': f.name,
                'description': f.description,
                'icon': f.icon,
            })
        content['sections'].append(section_data)

    # Features (преимущества)
    fb = LandingFeatureBlock.objects.first()
    if fb:
        content['features'] = {
            'headline': fb.headline,
            'title': fb.title,
            'description': fb.description,
            'items': [
                {'title': i.title, 'description': i.description, 'icon': i.icon}
                for i in fb.items.all()
            ],
        }

    # Testimonials
    tb = LandingTestimonialBlock.objects.first()
    if tb:
        items = []
        for t in LandingTestimonial.objects.all():
            avatar_url = t.get_avatar_url()
            items.append({
                'quote': t.quote,
                'user': {
                    'name': t.user_name,
                    'description': t.user_description,
                    **({'avatar': {'src': avatar_url}} if avatar_url else {}),
                },
            })
        content['testimonials'] = {
            'headline': tb.title,
            'title': tb.title,
            'description': tb.description,
            'items': items,
        }

    # Pricing
    pb = LandingPricingBlock.objects.first()
    if pb:
        plans = []
        for p in pb.plans.all():
            plan_data = {
                'title': p.title,
                'description': p.description,
                'price': {'month': p.price_month, 'year': p.price_year},
                'button': {'label': p.button_label, 'color': 'neutral', 'variant': 'solid' if p.highlight else 'outline'},
                'highlight': p.highlight,
                'scale': p.scale,
                'features': [f.text for f in p.features.all()],
            }
            plans.append(plan_data)
        content['pricing'] = {
            'title': pb.title,
            'description': pb.description,
            'plans': plans,
        }

    # FAQ
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

    # CTA
    cta = LandingCTA.objects.first()
    if cta:
        content['cta'] = {
            'title': cta.title,
            'description': cta.description,
            'links': [
                {'label': l.label, 'to': l.to, 'trailingIcon': l.trailing_icon or ''}
                for l in cta.links.all()
            ],
        }

    return content
