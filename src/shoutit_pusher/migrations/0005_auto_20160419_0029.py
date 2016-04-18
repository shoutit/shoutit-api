# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_pusher', '0004_auto_20160226_1929'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pusherchanneljoin',
            name='user',
            field=models.ForeignKey(related_name='joined_pusher_channels', to=settings.AUTH_USER_MODEL),
        ),
    ]
