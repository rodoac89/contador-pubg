from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_match_training'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='discarded',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='match',
            name='discarded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
