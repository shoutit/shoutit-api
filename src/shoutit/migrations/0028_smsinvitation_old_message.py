# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0027_auto_20150723_1523'),
    ]

    operations = [
        migrations.AddField(
            model_name='smsinvitation',
            name='old_message',
            field=models.CharField(default='', max_length=160, blank=True),
        ),
    ]
