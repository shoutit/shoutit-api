# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0025_auto_20160806_1511'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smsinvitation',
            name='link',
            field=models.CharField(default='', max_length=1000, blank=True),
        ),
    ]
