# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0018_auto_20150610_1152'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='featuredtag',
            unique_together=set([('country', 'state', 'city', 'rank')]),
        ),
    ]
