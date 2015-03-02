# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0020_auto_20150302_1541'),
    ]

    operations = [
        migrations.RenameField(
            model_name='currency',
            old_name='Code',
            new_name='code',
        ),
        migrations.RenameField(
            model_name='service',
            old_name='Code',
            new_name='code',
        ),
        migrations.RenameField(
            model_name='voucher',
            old_name='Code',
            new_name='code',
        ),
    ]
