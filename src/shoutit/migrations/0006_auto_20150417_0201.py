# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0005_auto_20150417_0147'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='video',
            name='item',
        ),
        migrations.RemoveField(
            model_name='video',
            name='shout',
        ),
        migrations.AddField(
            model_name='item',
            name='videos',
            field=models.ForeignKey(blank=True, to='shoutit.Video', null=True),
        ),
    ]
