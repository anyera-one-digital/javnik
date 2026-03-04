# Generated manually for landing app

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LandingImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='landing/', verbose_name='Изображение')),
                ('alt_text', models.CharField(blank=True, max_length=255, verbose_name='Описание')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')),
            ],
            options={
                'verbose_name': 'Изображение лендинга',
                'verbose_name_plural': 'Изображения лендинга',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='LandingPage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(default='index', unique=True, verbose_name='Идентификатор')),
                ('content', models.JSONField(blank=True, default=dict, help_text='JSON с блоками: title, description, seo, sections, features, testimonials, pricing, faq, cta', verbose_name='Контент')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Страница лендинга',
                'verbose_name_plural': 'Страницы лендинга',
            },
        ),
    ]
