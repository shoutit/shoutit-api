# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0054_facebook_la_upadtes'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='published_on',
            field=django.contrib.postgres.fields.hstore.HStoreField(default=dict, blank=True),
        ),
    ]
