# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0007_dbz2user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='image',
            field=models.URLField(default='https://user-image.static.shoutit.com/default_male.jpg', max_length=1024, blank=True),
        ),
    ]
