from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_user_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='show_public_schedule',
            field=models.BooleanField(
                default=True,
                verbose_name='Показывать расписание на публичной странице',
            ),
        ),
    ]
