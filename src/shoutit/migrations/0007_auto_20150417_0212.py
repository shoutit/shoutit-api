# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0006_auto_20150417_0201'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='videos',
        ),
        migrations.AddField(
            model_name='item',
            name='videos',
            field=models.ManyToManyField(to='shoutit.Video', null=True, blank=True),
        ),
    ]
