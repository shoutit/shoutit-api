# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0004_auto_20150510_1724'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='conversation',
            field=models.ForeignKey(related_name='messages', to='shoutit.Conversation'),
        ),
        migrations.AlterField(
            model_name='message',
            name='deleted_by',
            field=models.ManyToManyField(related_name='deleted_messages', through='shoutit.MessageDelete', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='message',
            name='read_by',
            field=models.ManyToManyField(related_name='read_messages', through='shoutit.MessageRead', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='messagedelete',
            name='conversation',
            field=models.ForeignKey(related_name='messages_deleted_set', to='shoutit.Conversation'),
        ),
        migrations.AlterField(
            model_name='messagedelete',
            name='user',
            field=models.ForeignKey(related_name='deleted_messages_set', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='messageread',
            name='conversation',
            field=models.ForeignKey(related_name='messages_read_set', to='shoutit.Conversation'),
        ),
        migrations.AlterField(
            model_name='messageread',
            name='user',
            field=models.ForeignKey(related_name='read_messages_set', to=settings.AUTH_USER_MODEL),
        ),
    ]
