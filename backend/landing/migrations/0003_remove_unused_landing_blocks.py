# Generated manually — удаление неиспользуемых блоков лендинга

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('landing', '0002_landing_blocks'),
    ]

    operations = [
        migrations.DeleteModel(name='LandingSectionFeature'),
        migrations.DeleteModel(name='LandingSection'),
        migrations.DeleteModel(name='LandingFeatureItem'),
        migrations.DeleteModel(name='LandingFeatureBlock'),
        migrations.DeleteModel(name='LandingTestimonial'),
        migrations.DeleteModel(name='LandingTestimonialBlock'),
        migrations.DeleteModel(name='LandingPricingPlanFeature'),
        migrations.DeleteModel(name='LandingPricingPlan'),
        migrations.DeleteModel(name='LandingPricingBlock'),
        migrations.DeleteModel(name='LandingCTALink'),
        migrations.DeleteModel(name='LandingCTA'),
        migrations.DeleteModel(name='LandingImage'),
    ]
