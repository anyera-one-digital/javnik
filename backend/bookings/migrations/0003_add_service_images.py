# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_workschedule_workbreak'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='cover_image',
            field=models.ImageField(blank=True, null=True, upload_to='services/covers/', verbose_name='Заглавное изображение'),
        ),
        migrations.CreateModel(
            name='ServiceImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='services/portfolio/', verbose_name='Изображение')),
                ('order', models.IntegerField(default=0, verbose_name='Порядок сортировки')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='portfolio_images', to='bookings.service', verbose_name='Услуга')),
            ],
            options={
                'verbose_name': 'Изображение услуги',
                'verbose_name_plural': 'Изображения услуг',
                'ordering': ['order', 'created_at'],
            },
        ),
    ]
