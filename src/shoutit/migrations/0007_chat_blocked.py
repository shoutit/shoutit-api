# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.postgres.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0006_auto_20160511_1210'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='blocked',
            field=django.contrib.postgres.fields.ArrayField(default=list, size=None, base_field=models.UUIDField(), blank=True),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='last_message',
            field=models.OneToOneField(related_name='+', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='shoutit.Message'),
        ),
    ]
