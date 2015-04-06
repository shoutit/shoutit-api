# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conversation2',
            name='object_id',
            field=models.UUIDField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='object_id',
            field=models.UUIDField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='messageattachment',
            name='object_id',
            field=models.UUIDField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='object_id',
            field=models.UUIDField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='payment',
            name='object_id',
            field=models.UUIDField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='object_id',
            field=models.UUIDField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='stream2',
            name='object_id',
            field=models.UUIDField(null=True, blank=True),
        ),
    ]
