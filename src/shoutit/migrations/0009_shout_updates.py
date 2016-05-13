# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0008_profile_defaults'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='muted',
            new_name='is_muted',
        ),
        migrations.RenameField(
            model_name='post',
            old_name='date_published',
            new_name='published_at',
        ),
        migrations.RenameField(
            model_name='shout',
            old_name='expiry_date',
            new_name='expires_at',
        ),
        migrations.RenameField(
            model_name='shout',
            old_name='tags2',
            new_name='filters',
        ),
    ]
