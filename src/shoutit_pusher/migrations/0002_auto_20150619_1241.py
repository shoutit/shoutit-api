# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_pusher', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pusherchannel',
            name='devices',
        ),
        migrations.RemoveField(
            model_name='pusherchanneljoin',
            name='channel',
        ),
        migrations.RemoveField(
            model_name='pusherchanneljoin',
            name='device',
        ),
        migrations.RemoveField(
            model_name='pusherdevice',
            name='user',
        ),
        migrations.DeleteModel(
            name='PusherChannel',
        ),
        migrations.DeleteModel(
            name='PusherChannelJoin',
        ),
        migrations.DeleteModel(
            name='PusherDevice',
        ),
    ]
