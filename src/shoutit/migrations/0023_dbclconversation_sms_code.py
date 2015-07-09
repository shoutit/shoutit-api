# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0022_auto_20150708_1112'),
    ]

    operations = [
        migrations.AddField(
            model_name='dbclconversation',
            name='sms_code',
            field=models.CharField(max_length=10, null=True, blank=True),
        ),
    ]
