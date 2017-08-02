# -*- coding: utf-8 -*-
from django.db import migrations

from ..models import VideoClient
from ..settings import SHOUTIT_TWILIO_SETTINGS


def set_new_ttl(apps, schema_editor):
    VideoClient.objects.update(ttl=SHOUTIT_TWILIO_SETTINGS['TOKEN_TTL'])


def undo_reset_ttl(apps, schema_editor):
    VideoClient.objects.update(ttl=3600)


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit_twilio', '0002_auto_20160502_2328'),
    ]

    operations = [
        migrations.RunPython(set_new_ttl, undo_reset_ttl)
    ]
