# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from shoutit.models import Listen, Message


def fill_actions(apps, schema_editor):

    # Fill Listen locations
    for l in Listen.objects.all():
        l.save()

    # Fill Message locations
    for m in Message.objects.all():
        m.save()


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0042_auto_20151013_1718'),
    ]

    operations = [
        migrations.RunPython(fill_actions)
    ]
