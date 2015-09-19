# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import shoutit.models.base


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0019_auto_20150610_1402'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', shoutit.models.base.ShoutitUserManager()),
            ],
        ),
    ]
