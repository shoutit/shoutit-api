# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from shoutit.models import Message


def fill_actions(apps, schema_editor):

    # Fill Message locations
    for m in Message.objects.all():
        m.save()


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0042_action_message'),
    ]

    operations = [
        migrations.RunPython(fill_actions)
    ]
