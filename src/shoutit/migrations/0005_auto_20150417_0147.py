# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0004_auto_20150417_0143'),
    ]

    operations = [
        migrations.RenameField(
            model_name='experience',
            old_name='State',
            new_name='state',
        ),
        migrations.RenameField(
            model_name='item',
            old_name='State',
            new_name='state',
        ),
        migrations.RenameField(
            model_name='subscription',
            old_name='State',
            new_name='state',
        ),
    ]
