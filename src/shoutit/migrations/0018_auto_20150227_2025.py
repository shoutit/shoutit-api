# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0017_auto_20150224_2105'),
    ]

    operations = [
        migrations.RenameField(
            model_name='conversation',
            old_name='IsRead',
            new_name='is_read',
        ),
        migrations.RenameField(
            model_name='message',
            old_name='IsRead',
            new_name='is_read',
        ),
        migrations.RenameField(
            model_name='notification',
            old_name='IsRead',
            new_name='is_read',
        ),
        migrations.AlterField(
            model_name='notification',
            name='ToUser',
            field=models.ForeignKey(related_name='notifications', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
