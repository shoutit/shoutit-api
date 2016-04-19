# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_pusher', '0005_auto_20160419_0029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pusherchannel',
            name='users',
            field=models.ManyToManyField(related_name='joined_pusher_channels', through='shoutit_pusher.PusherChannelJoin', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='pusherchanneljoin',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
