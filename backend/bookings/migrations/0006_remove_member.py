from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0005_event_price_nullable_service'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='member',
        ),
        migrations.RemoveField(
            model_name='event',
            name='member',
        ),
        migrations.DeleteModel(
            name='Member',
        ),
    ]
