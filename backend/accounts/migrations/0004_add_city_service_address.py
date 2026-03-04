# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_add_specialty_bio'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='city',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Город'),
        ),
        migrations.AddField(
            model_name='user',
            name='service_address',
            field=models.TextField(blank=True, null=True, verbose_name='Адрес оказания услуг'),
        ),
    ]
