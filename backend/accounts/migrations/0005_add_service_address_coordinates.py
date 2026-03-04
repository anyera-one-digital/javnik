# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_add_city_service_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='service_address_lat',
            field=models.FloatField(blank=True, null=True, verbose_name='Широта адреса'),
        ),
        migrations.AddField(
            model_name='user',
            name='service_address_lon',
            field=models.FloatField(blank=True, null=True, verbose_name='Долгота адреса'),
        ),
    ]
