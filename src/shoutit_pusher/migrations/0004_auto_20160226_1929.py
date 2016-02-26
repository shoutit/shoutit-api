# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_pusher', '0003_auto_20150619_1243'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pusherchannel',
            name='users',
            field=models.ManyToManyField(related_name='channels', through='shoutit_pusher.PusherChannelJoin', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
