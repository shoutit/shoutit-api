# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0031_update_hvad_master'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='predefinedcity',
            unique_together=set([('country', 'postal_code', 'state', 'city'), ('latitude', 'longitude')]),
        ),
    ]
