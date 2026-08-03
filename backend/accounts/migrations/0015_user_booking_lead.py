from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_user_show_public_reviews_portfolio'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='booking_lead',
            field=models.CharField(
                default='same_day_1h',
                help_text='Как рано клиент может записаться: за час, на следующий день и т.д.',
                max_length=32,
                verbose_name='Минимальный срок до записи',
            ),
        ),
    ]
