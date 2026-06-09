from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('landing', '0003_remove_unused_landing_blocks'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalPage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(choices=[('privacy', 'Политика конфиденциальности'), ('terms', 'Пользовательское соглашение')], max_length=32, unique=True, verbose_name='Страница')),
                ('title', models.CharField(max_length=500, verbose_name='Заголовок')),
                ('subtitle', models.CharField(blank=True, max_length=500, verbose_name='Подзаголовок')),
                ('content', models.TextField(help_text='HTML-разметка тела страницы (без заголовка h1). Допустимы теги: section, h2, p, ul, ol, li, a, strong, table.', verbose_name='Содержимое (HTML)')),
                ('seo_title', models.CharField(blank=True, max_length=255, verbose_name='SEO заголовок')),
                ('seo_description', models.TextField(blank=True, verbose_name='SEO описание')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Юридическая страница',
                'verbose_name_plural': 'Юридические страницы',
            },
        ),
    ]
