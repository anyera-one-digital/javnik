from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_cleanup_duplicate_specialties'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='show_public_reviews',
            field=models.BooleanField(
                default=True,
                verbose_name='Показывать отзывы на публичной странице',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='show_public_portfolio',
            field=models.BooleanField(
                default=True,
                verbose_name='Показывать портфолио на публичной странице',
            ),
        ),
    ]
