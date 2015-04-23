# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0004_auto_20150422_1635'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='event_type',
            field=models.IntegerField(default=0, choices=[(0, 'Listen to User'), (1, 'Listen to Tag'), (2, 'Shout Offer'), (3, 'Shout Request'), (4, 'Shout Experience'), (5, 'Share Experience'), (6, 'Comment'), (7, 'Post Deal'), (8, 'Buy Deal'), (9, 'Listen to Page')]),
        ),
    ]
