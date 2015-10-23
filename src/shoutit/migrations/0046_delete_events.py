# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def delete_event_posts(apps, schema_editor):
    Post = apps.get_model("shoutit", "Post")
    Post.objects.filter(type=4).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0043_fill_actions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='event',
            name='post_ptr',
        ),
        migrations.AlterField(
            model_name='post',
            name='type',
            field=models.IntegerField(default=0, db_index=True, choices=[(0, 'request'), (1, 'offer'), (2, 'Experience'), (3, 'Deal')]),
        ),
        migrations.DeleteModel(
            name='Event',
        ),
        migrations.RunPython(delete_event_posts)
    ]
