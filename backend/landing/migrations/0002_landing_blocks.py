# Migration: replace LandingPage with block-based models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('landing', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(name='LandingPage'),
        migrations.CreateModel(
            name='LandingHero',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500, verbose_name='Заголовок')),
                ('description', models.TextField(verbose_name='Описание')),
                ('seo_title', models.CharField(blank=True, max_length=255, verbose_name='SEO заголовок')),
                ('seo_description', models.TextField(blank=True, verbose_name='SEO описание')),
            ],
            options={'verbose_name': 'Главный экран (Hero)', 'verbose_name_plural': 'Главный экран (Hero)'},
        ),
        migrations.CreateModel(
            name='LandingSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500, verbose_name='Заголовок')),
                ('description', models.TextField(verbose_name='Описание')),
                ('section_id', models.CharField(blank=True, max_length=100, verbose_name='ID для якоря')),
                ('image', models.ImageField(blank=True, null=True, upload_to='landing/sections/', verbose_name='Изображение')),
                ('image_url', models.URLField(blank=True, max_length=500, verbose_name='Или URL изображения')),
                ('orientation', models.CharField(choices=[('horizontal', 'Горизонтально'), ('vertical', 'Вертикально')], default='horizontal', max_length=20, verbose_name='Ориентация')),
                ('reverse', models.BooleanField(default=False, verbose_name='Порядок: картинка справа')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
            ],
            options={'verbose_name': 'Секция (блок с картинкой и пунктами)', 'verbose_name_plural': 'Секции', 'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='LandingFeatureBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('headline', models.CharField(blank=True, max_length=255, verbose_name='Подзаголовок')),
                ('title', models.CharField(max_length=500, verbose_name='Заголовок')),
                ('description', models.TextField(verbose_name='Описание')),
            ],
            options={'verbose_name': 'Блок «Преимущества»', 'verbose_name_plural': 'Блок «Преимущества»'},
        ),
        migrations.CreateModel(
            name='LandingTestimonialBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Заголовок')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
            ],
            options={'verbose_name': 'Блок «Истории успеха»', 'verbose_name_plural': 'Блок «Истории успеха»'},
        ),
        migrations.CreateModel(
            name='LandingPricingBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Заголовок')),
                ('description', models.TextField(verbose_name='Описание')),
            ],
            options={'verbose_name': 'Блок «Тарифы»', 'verbose_name_plural': 'Блок «Тарифы»'},
        ),
        migrations.CreateModel(
            name='LandingFAQBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Заголовок')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
            ],
            options={'verbose_name': 'Блок «Вопросы-ответы»', 'verbose_name_plural': 'Блок «Вопросы-ответы»'},
        ),
        migrations.CreateModel(
            name='LandingCTA',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500, verbose_name='Заголовок')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
            ],
            options={'verbose_name': 'Блок «Призыв к действию» (CTA)', 'verbose_name_plural': 'Блок «Призыв к действию» (CTA)'},
        ),
        migrations.CreateModel(
            name='LandingSectionFeature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Название')),
                ('description', models.TextField(verbose_name='Описание')),
                ('icon', models.CharField(default='i-lucide-circle', max_length=100, verbose_name='Иконка (например i-lucide-scissors)')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='features', to='landing.landingsection', verbose_name='Секция')),
            ],
            options={'verbose_name': 'Пункт секции', 'verbose_name_plural': 'Пункты секции', 'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='LandingFeatureItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Заголовок')),
                ('description', models.TextField(verbose_name='Описание')),
                ('icon', models.CharField(default='i-lucide-circle', max_length=100, verbose_name='Иконка')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('block', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='landing.landingfeatureblock', verbose_name='Блок')),
            ],
            options={'verbose_name': 'Пункт преимущества', 'verbose_name_plural': 'Пункты преимуществ', 'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='LandingTestimonial',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quote', models.TextField(verbose_name='Цитата')),
                ('user_name', models.CharField(max_length=255, verbose_name='Имя')),
                ('user_description', models.CharField(max_length=255, verbose_name='Профессия/описание')),
                ('user_avatar', models.ImageField(blank=True, null=True, upload_to='landing/testimonials/', verbose_name='Фото')),
                ('user_avatar_url', models.URLField(blank=True, max_length=500, verbose_name='Или URL фото')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
            ],
            options={'verbose_name': 'Отзыв', 'verbose_name_plural': 'Отзывы', 'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='LandingPricingPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Название')),
                ('description', models.TextField(verbose_name='Описание')),
                ('price_month', models.CharField(max_length=50, verbose_name='Цена/месяц')),
                ('price_year', models.CharField(max_length=50, verbose_name='Цена/год')),
                ('button_label', models.CharField(default='Начать', max_length=100, verbose_name='Текст кнопки')),
                ('highlight', models.BooleanField(default=False, verbose_name='Выделить')),
                ('scale', models.BooleanField(default=False, verbose_name='Увеличить')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('block', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plans', to='landing.landingpricingblock', verbose_name='Блок')),
            ],
            options={'verbose_name': 'Тарифный план', 'verbose_name_plural': 'Тарифные планы', 'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='LandingPricingPlanFeature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.CharField(max_length=255, verbose_name='Пункт')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='features', to='landing.landingpricingplan', verbose_name='План')),
            ],
            options={'verbose_name': 'Пункт тарифа', 'verbose_name_plural': 'Пункты тарифов', 'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='LandingFAQItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=500, verbose_name='Вопрос')),
                ('content', models.TextField(verbose_name='Ответ')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('block', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='landing.landingfaqblock', verbose_name='Блок')),
            ],
            options={'verbose_name': 'Вопрос-ответ', 'verbose_name_plural': 'Вопросы-ответы', 'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='LandingCTALink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=255, verbose_name='Текст кнопки')),
                ('to', models.CharField(blank=True, max_length=255, verbose_name='Ссылка')),
                ('trailing_icon', models.CharField(blank=True, max_length=100, verbose_name='Иконка (например i-lucide-arrow-right)')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('block', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='landing.landingcta', verbose_name='Блок')),
            ],
            options={'verbose_name': 'Кнопка CTA', 'verbose_name_plural': 'Кнопки CTA', 'ordering': ['order']},
        ),
    ]
