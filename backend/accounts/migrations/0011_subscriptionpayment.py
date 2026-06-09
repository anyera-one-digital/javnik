import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_user_show_public_schedule'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscriptionPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=36, unique=True, verbose_name='OrderId')),
                ('payment_id', models.CharField(blank=True, default='', max_length=32, verbose_name='PaymentId T‑Bank')),
                ('amount', models.PositiveIntegerField(verbose_name='Сумма, коп.')),
                ('billing_period', models.CharField(choices=[('month', 'Месяц'), ('year', 'Год')], max_length=8, verbose_name='Период')),
                ('status', models.CharField(choices=[('new', 'Создан'), ('pending', 'Ожидает оплаты'), ('confirmed', 'Оплачен'), ('rejected', 'Отклонён'), ('canceled', 'Отменён')], default='new', max_length=16, verbose_name='Статус')),
                ('payment_url', models.URLField(blank=True, default='', verbose_name='URL оплаты')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создан')),
                ('paid_at', models.DateTimeField(blank=True, null=True, verbose_name='Оплачен')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscription_payments', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Платёж подписки',
                'verbose_name_plural': 'Платежи подписки',
                'ordering': ['-created_at'],
            },
        ),
    ]
