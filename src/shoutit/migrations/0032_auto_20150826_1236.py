# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_pgjson.fields
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('shoutit', '0031_auto_20150823_1739'),
    ]

    operations = [
        migrations.CreateModel(
            name='PushBroadcast',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('object_id', models.UUIDField(null=True, blank=True)),
                ('message', models.TextField(max_length=300, blank=True)),
                ('conditions', django_pgjson.fields.JsonField(default=dict, blank=True)),
                ('data', django_pgjson.fields.JsonField(default=dict, blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('user', models.ForeignKey(related_name='broadcasts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, 'new_listen'), (1, 'new_message'), (2, 'broadcast'), (3, 'profile_update'), (4, 'Experience'), (5, 'Experience Shared'), (6, 'Comment')]),
        ),
    ]
