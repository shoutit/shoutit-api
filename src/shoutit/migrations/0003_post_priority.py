# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def set_priority(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Shout = apps.get_model("shoutit", "Shout")
    Shout.objects.filter(is_sss=True).update(priority=-10)


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0002_auto_20150502_1819'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='priority',
            field=models.SmallIntegerField(default=0),
        ),
        migrations.RunPython(set_priority),
    ]
