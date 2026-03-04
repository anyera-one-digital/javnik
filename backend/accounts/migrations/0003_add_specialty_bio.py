# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_managers_alter_user_username'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='specialty',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Специальность'),
        ),
        migrations.AddField(
            model_name='user',
            name='bio',
            field=models.TextField(blank=True, null=True, verbose_name='О себе'),
        ),
    ]
