# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0029_auto_20160812_1244'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True)),
                ('modified_at', models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True)),
                ('used_count', models.SmallIntegerField(default=0)),
                ('page_admin_user', models.ForeignKey(related_name='pages_authtokens', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
