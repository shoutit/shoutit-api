# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import re
from django.conf import settings
import django.core.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PusherChannel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('type', models.SmallIntegerField(choices=[(0, 'public'), (1, 'private'), (2, 'presence')])),
                ('name', models.CharField(unique=True, max_length=164, validators=[django.core.validators.RegexValidator(re.compile('\\A[-a-zA-Z0-9_=@,.;]+\\Z'))])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PusherChannelJoin',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('channel', models.ForeignKey(to='shoutit_pusher.PusherChannel')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PusherDevice',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('socket_id', models.CharField(unique=True, max_length=64, validators=[django.core.validators.RegexValidator(re.compile('\\A\\d+\\.\\d+\\Z'))])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='pusherchanneljoin',
            name='device',
            field=models.ForeignKey(to='shoutit_pusher.PusherDevice'),
        ),
        migrations.AddField(
            model_name='pusherchannel',
            name='devices',
            field=models.ManyToManyField(related_name='channels', through='shoutit_pusher.PusherChannelJoin', to='shoutit_pusher.PusherDevice'),
        ),
    ]
