# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0039_auto_20151012_0112'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='page_admin_user',
            field=models.ForeignKey(related_name='pages_posts', to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
