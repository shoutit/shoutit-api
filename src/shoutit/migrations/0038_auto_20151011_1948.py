# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0037_auto_20151010_1907'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pageadmin',
            old_name='user',
            new_name='admin',
        ),
    ]
