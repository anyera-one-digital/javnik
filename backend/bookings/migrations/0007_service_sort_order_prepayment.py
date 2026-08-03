# Generated manually for Service.sort_order and Service.prepayment

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0006_remove_member'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='service',
            options={
                'ordering': ['sort_order', 'id'],
                'verbose_name': 'Услуга',
                'verbose_name_plural': 'Услуги',
            },
        ),
        migrations.AddField(
            model_name='service',
            name='prepayment',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=10,
                verbose_name='Предоплата',
            ),
        ),
        migrations.AddField(
            model_name='service',
            name='sort_order',
            field=models.IntegerField(default=0, verbose_name='Порядок сортировки'),
        ),
    ]
