# Generated by Django 3.1 on 2020-08-26 03:45

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrud_django', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcetype',
            name='etag',
            field=models.CharField(default='XXXX', max_length=40),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='resourcetype',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
