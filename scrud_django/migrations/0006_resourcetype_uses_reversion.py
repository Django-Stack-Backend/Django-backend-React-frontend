# Generated by Django 2.2.11 on 2021-05-18 22:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrud_django', '0005_fix_resource_content_column_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='resourcetype',
            name='uses_reversion',
            field=models.BooleanField(default=True),
        ),
    ]
