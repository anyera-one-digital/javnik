# Generated manually

from django.db import migrations, models


def create_specialty_models_and_migrate_data(apps, schema_editor):
    """Создаём категории, специальности и переносим данные из specialty_old."""
    SpecialtyCategory = apps.get_model('accounts', 'SpecialtyCategory')
    Specialty = apps.get_model('accounts', 'Specialty')
    User = apps.get_model('accounts', 'User')

    # Создаём категорию "Прочее" для старых произвольных специальностей
    other_cat, _ = SpecialtyCategory.objects.get_or_create(
        name='Прочее',
        defaults={'order': 999}
    )

    # Создаём базовые категории и специальности
    beauty_cat, _ = SpecialtyCategory.objects.get_or_create(
        name='Бьюти сфера',
        defaults={'order': 0}
    )
    for name, order in [('Парикмахер', 0), ('Визажист', 1), ('Стилист', 2), ('Мастер-колорист', 3), ('Барбер', 4)]:
        Specialty.objects.get_or_create(category=beauty_cat, name=name, defaults={'order': order})

    # Переносим пользователей с specialty_old
    for user in User.objects.exclude(specialty_old__isnull=True).exclude(specialty_old=''):
        name = user.specialty_old.strip()
        if not name:
            continue
        specialty, _ = Specialty.objects.get_or_create(
            category=other_cat,
            name=name,
            defaults={'order': 0}
        )
        user.specialty = specialty
        user.save(update_fields=['specialty'])


def reverse_migration(apps, schema_editor):
    """Откат: записываем название специальности обратно в specialty_old."""
    User = apps.get_model('accounts', 'User')
    for user in User.objects.all():
        user.specialty_old = user.specialty.name if user.specialty else ''
        user.save(update_fields=['specialty_old'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_add_service_address_coordinates'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpecialtyCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
            ],
            options={
                'verbose_name': 'Категория специальностей',
                'verbose_name_plural': 'Категории специальностей',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Specialty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('category', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='specialties', to='accounts.specialtycategory', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Специальность',
                'verbose_name_plural': 'Специальности',
                'ordering': ['category', 'order', 'name'],
            },
        ),
        migrations.RenameField(
            model_name='user',
            old_name='specialty',
            new_name='specialty_old',
        ),
        migrations.AddField(
            model_name='user',
            name='specialty',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='users', to='accounts.specialty', verbose_name='Специальность'),
        ),
        migrations.RunPython(create_specialty_models_and_migrate_data, reverse_migration),
        migrations.RemoveField(
            model_name='user',
            name='specialty_old',
        ),
    ]
