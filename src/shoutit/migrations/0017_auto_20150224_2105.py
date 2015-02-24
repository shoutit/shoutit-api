# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0016_auto_20150224_2105'),
    ]

    operations = [
        migrations.RenameField(
            model_name='message2',
            old_name='message',
            new_name='text',
        ),
    ]
