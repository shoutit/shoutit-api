# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0005_auto_20150423_1949'),
    ]

    operations = [
        migrations.RenameField(
            model_name='predefinedcity',
            old_name='Approved',
            new_name='approved',
        ),
    ]
