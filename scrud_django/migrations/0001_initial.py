# Generated by Django 3.0.8 on 2020-08-10 20:42

import django.db.models.deletion
from django.db import migrations, models
from django_jsonfield_backport.models import JSONField


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Resource',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('content', JSONField(default=dict)),
                ('modified_at', models.DateTimeField()),
                ('etag', models.CharField(max_length=40)),
            ],
        ),
        migrations.CreateModel(
            name='ResourceType',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('type_uri', models.URLField()),
                ('slug', models.CharField(max_length=255, null=True)),
                ('schema_uri', models.URLField(null=True)),
                ('context_uri', models.URLField(null=True)),
                (
                    'context',
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='resource_type_context',
                        to='scrud_django.Resource',
                        verbose_name='context resource type',
                    ),
                ),
                (
                    'schema',
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='resource_type_schema',
                        to='scrud_django.Resource',
                        verbose_name='schema resource type',
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name='resource',
            name='resource_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='resource_type',
                to='scrud_django.ResourceType',
                verbose_name='resource type',
            ),
        ),
    ]