# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from shoutit.models import Page, Profile, Tag


def fill_actions(apps, schema_editor):
    Page.objects.filter(image="https://tag-image.static.shoutit.com/default.jpg").update(image="")
    Profile.objects.filter(image="https://user-image.static.shoutit.com/default_male.jpg").update(image="")
    Tag.objects.filter(image="https://tag-image.static.shoutit.com/default.jpg").update(image="")


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0059_category_icon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tag',
            name='image',
            field=models.URLField(default='', max_length=1024, blank=True),
        ),
        migrations.RunPython(fill_actions)
    ]
