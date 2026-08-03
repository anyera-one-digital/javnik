from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0007_service_sort_order_prepayment'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='status_manual',
            field=models.BooleanField(default=False, verbose_name='Статус задан вручную'),
        ),
    ]
