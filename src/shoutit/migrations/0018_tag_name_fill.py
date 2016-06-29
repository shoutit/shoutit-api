# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import F


def fill_names(apps, schema_editor):
    Tag = apps.get_model('shoutit', 'Tag')
    Tag.objects.all().update(name2=F('name'), slug=F('name'))

    TagKey = apps.get_model('shoutit', 'TagKey')
    TagKey.objects.all().update(name=F('slug'))


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit', '0017_cat_tag_key'),
    ]

    operations = [
        migrations.RunPython(fill_names),
        migrations.RemoveField(model_name='tag', name='name'),
        migrations.RenameField(model_name='tag', old_name='name2', new_name='name')
    ]
