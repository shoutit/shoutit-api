# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0004_auto_20150221_0143'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='Type',
            field=models.IntegerField(default=0, db_index=True, choices=[(0, b'request'), (1, b'offer'), (2, b'Experience'), (3, b'Deal'), (4, b'Event')]),
            preserve_default=True,
        ),
    ]
