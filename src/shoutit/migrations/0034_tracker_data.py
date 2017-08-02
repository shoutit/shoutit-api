# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid
import django_pgjson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0033_currency_usd'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrackerData',
            fields=[
                ('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('created_at', models.DateTimeField(verbose_name='Creation time', null=True, db_index=True, auto_now_add=True)),
                ('modified_at', models.DateTimeField(verbose_name='Modification time', null=True, db_index=True, auto_now=True)),
                ('date', models.DateField()),
                ('data', django_pgjson.fields.JsonField(blank=True, default=dict)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
