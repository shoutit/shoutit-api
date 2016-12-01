# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_pgjson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0030_auth_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='stats_store',
            field=django_pgjson.fields.JsonField(default=dict, blank=True),
        ),
    ]
