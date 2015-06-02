# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def set_address(apps, schema_editor):
    # We use the historical version of models.
    Post = apps.get_model("shoutit", "Post")
    Post.objects.filter(city=None).update(city='')
    Post.objects.filter(country=None).update(country='')
    Post.objects.filter(address=None).update(address='')


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit', '0011_featuredtag_title'),
    ]

    operations = [
        migrations.RunPython(set_address),
    ]
