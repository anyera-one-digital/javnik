# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0004_review'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='service',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='events',
                to='bookings.service',
                verbose_name='Услуга'
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                verbose_name='Стоимость'
            ),
        ),
    ]
