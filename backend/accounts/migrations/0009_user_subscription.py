# Generated manually for subscription fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_user_work_schedule_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='subscription_plan',
            field=models.CharField(
                choices=[('free', 'Free'), ('pro', 'Pro')],
                default='free',
                max_length=8,
                verbose_name='Тариф (назначенный)',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='subscription_expires_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Для Pro: дата окончания. Пусто — без срока (бессрочный Pro).',
                null=True,
                verbose_name='Pro действует до',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='subscription_started_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Начало текущего периода Pro',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='subscription_granted_via',
            field=models.CharField(
                blank=True,
                choices=[
                    ('trial', 'Пробный период'),
                    ('admin', 'Вручную (админка)'),
                    ('payment', 'Оплата'),
                ],
                default='',
                max_length=16,
                verbose_name='Источник Pro',
            ),
        ),
    ]
