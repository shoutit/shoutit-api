# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0010_new_notifications_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='linkedfacebookaccount',
            name='friends',
            field=django.contrib.postgres.fields.ArrayField(default=list, size=None, base_field=models.CharField(max_length=24), blank=True),
        ),
    ]
