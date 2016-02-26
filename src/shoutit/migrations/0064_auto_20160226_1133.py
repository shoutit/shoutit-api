# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0063_auto_20160226_0251'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='tags',
            field=models.ManyToManyField(related_name='category', to='shoutit.Tag', blank=True),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='users',
            field=models.ManyToManyField(related_name='conversations', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='deleted_by',
            field=models.ManyToManyField(related_name='deleted_messages', through='shoutit.MessageDelete', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='message',
            name='read_by',
            field=models.ManyToManyField(related_name='read_messages', through='shoutit.MessageRead', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='page',
            name='admins',
            field=models.ManyToManyField(related_name='pages', through='shoutit.PageAdmin', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='permissions',
            field=models.ManyToManyField(to='shoutit.Permission', through='shoutit.UserPermission', blank=True),
        ),
    ]
