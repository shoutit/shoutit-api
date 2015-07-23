# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0026_auto_20150722_2302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smsinvitation',
            name='message',
            field=models.CharField(max_length=160),
        ),
        migrations.AlterField(
            model_name='smsinvitation',
            name='mobile',
            field=models.CharField(unique=True, max_length=20),
        ),
    ]
