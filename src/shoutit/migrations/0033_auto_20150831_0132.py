# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def remove_duplicates(apps, schema_editor):
    GoogleLocation = apps.get_model("shoutit", "GoogleLocation")
    last_seen_latitude = None
    rows = GoogleLocation.objects.all().order_by('latitude')
    for row in rows:
        if row.latitude == last_seen_latitude:
            row.delete()
        else:
            last_seen_latitude = row.latitude


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit', '0032_auto_20150826_1236'),
    ]

    operations = [
        migrations.RunPython(remove_duplicates),
        migrations.AlterUniqueTogether(
            name='googlelocation',
            unique_together=set([('country', 'state', 'city', 'postal_code', 'latitude', 'longitude')]),
        ),
    ]
