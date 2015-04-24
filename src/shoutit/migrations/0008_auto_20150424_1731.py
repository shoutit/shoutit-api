# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0007_auto_20150424_1455'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='image',
            field=models.URLField(default='https://user-image.static.shoutit.com/9ca75a6a-fc7e-48f7-9b25-ec71783c28f5-1428689093983.jpg', max_length=1024, blank=True),
        ),
    ]
