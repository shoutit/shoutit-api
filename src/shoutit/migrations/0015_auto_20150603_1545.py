# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0014_auto_20150602_0034'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='predefinedcity',
            unique_together=set([('country', 'postal_code', 'state', 'city')]),
        ),
        migrations.RemoveField(
            model_name='predefinedcity',
            name='city_encoded',
        ),
    ]
