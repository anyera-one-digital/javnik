# Generated manually — расширение справочника специальностей

from django.db import migrations


CATEGORIES = [
    {
        'name': 'Бьюти',
        'order': 0,
        'legacy_names': ['Бьюти сфера'],
        'specialties': [
            ('Парикмахер', 0),
            ('Барбер', 1),
            ('Мастер-колорист', 2),
            ('Стилист', 3),
            ('Визажист', 4),
            ('Мастер маникюра', 5),
            ('Мастер педикюра', 6),
            ('Мастер маникюра и педикюра', 7),
            ('Бровист', 8),
            ('Lash-мастер', 9),
            ('Косметолог', 10),
            ('Мастер депиляции', 11),
            ('Массажист', 12),
            ('Мастер перманентного макияжа', 13),
        ],
    },
    {
        'name': 'Здоровье и фитнес',
        'order': 1,
        'legacy_names': [],
        'specialties': [
            ('Психолог', 0),
            ('Психотерапевт', 1),
            ('Нутрициолог', 2),
            ('Персональный тренер', 3),
            ('Инструктор йоги', 4),
            ('Инструктор пилатеса', 5),
        ],
    },
    {
        'name': 'Обучение и консультации',
        'order': 2,
        'legacy_names': [],
        'specialties': [
            ('Репетитор', 0),
            ('Преподаватель иностранного языка', 1),
            ('Бизнес-коуч', 2),
            ('Юрист (консультации)', 3),
        ],
    },
    {
        'name': 'Творчество и услуги',
        'order': 3,
        'legacy_names': [],
        'specialties': [
            ('Фотограф', 0),
            ('Мастер татуировки', 1),
        ],
    },
    {
        'name': 'Прочее',
        'order': 99,
        'legacy_names': [],
        'specialties': [
            ('Другое', 0),
        ],
    },
]


def seed_specialties(apps, schema_editor):
    SpecialtyCategory = apps.get_model('accounts', 'SpecialtyCategory')
    Specialty = apps.get_model('accounts', 'Specialty')

    for category_data in CATEGORIES:
        category = SpecialtyCategory.objects.filter(name=category_data['name']).first()
        if category is None:
            for legacy_name in category_data['legacy_names']:
                category = SpecialtyCategory.objects.filter(name=legacy_name).first()
                if category is not None:
                    category.name = category_data['name']
                    category.order = category_data['order']
                    category.save(update_fields=['name', 'order'])
                    break

        if category is None:
            category = SpecialtyCategory.objects.create(
                name=category_data['name'],
                order=category_data['order'],
            )
        else:
            if category.order != category_data['order']:
                category.order = category_data['order']
                category.save(update_fields=['order'])

        for specialty_name, specialty_order in category_data['specialties']:
            specialty, created = Specialty.objects.get_or_create(
                category=category,
                name=specialty_name,
                defaults={'order': specialty_order},
            )
            if not created and specialty.order != specialty_order:
                specialty.order = specialty_order
                specialty.save(update_fields=['order'])


def unseed_specialties(apps, schema_editor):
    """Удаляем только добавленные этой миграцией специальности без пользователей."""
    SpecialtyCategory = apps.get_model('accounts', 'SpecialtyCategory')
    Specialty = apps.get_model('accounts', 'Specialty')
    User = apps.get_model('accounts', 'User')

    added_names = {
        name
        for category_data in CATEGORIES
        for name, _order in category_data['specialties']
    }

    for specialty in Specialty.objects.filter(name__in=added_names):
        if User.objects.filter(specialty=specialty).exists():
            continue
        specialty.delete()

    for category_data in CATEGORIES:
        if category_data['name'] == 'Прочее':
            continue
        category = SpecialtyCategory.objects.filter(name=category_data['name']).first()
        if category and not Specialty.objects.filter(category=category).exists():
            category.delete()

    beauty = SpecialtyCategory.objects.filter(name='Бьюти').first()
    if beauty and not Specialty.objects.filter(category=beauty).exists():
        beauty.name = 'Бьюти сфера'
        beauty.save(update_fields=['name'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_subscriptionpayment'),
    ]

    operations = [
        migrations.RunPython(seed_specialties, unseed_specialties),
    ]
