# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0006_auto_20150416_1147'),
    ]

    operations = [
        migrations.AddField(
            model_name='shout',
            name='category',
            field=models.ForeignKey(related_name='shouts', to='shoutit.Category', null=True),
        ),
    ]
