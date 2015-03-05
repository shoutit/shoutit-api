# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0026_auto_20150305_1834'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message2',
            name='user',
            field=models.ForeignKey(related_name='+', default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
