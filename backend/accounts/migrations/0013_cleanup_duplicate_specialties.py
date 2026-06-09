# Generated manually — перенос пользователей с дубликатов из «Прочее»

from django.db import migrations


def cleanup_duplicate_specialties(apps, schema_editor):
    SpecialtyCategory = apps.get_model('accounts', 'SpecialtyCategory')
    Specialty = apps.get_model('accounts', 'Specialty')
    User = apps.get_model('accounts', 'User')

    other_cat = SpecialtyCategory.objects.filter(name='Прочее').first()
    if other_cat is None:
        return

    for specialty in Specialty.objects.filter(category=other_cat).exclude(name='Другое'):
        canonical = (
            Specialty.objects.filter(name=specialty.name)
            .exclude(category=other_cat)
            .order_by('category__order', 'order', 'id')
            .first()
        )
        if canonical is None:
            continue

        User.objects.filter(specialty=specialty).update(specialty=canonical)
        specialty.delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_seed_specialties'),
    ]

    operations = [
        migrations.RunPython(cleanup_duplicate_specialties, noop_reverse),
    ]
