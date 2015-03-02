# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0019_auto_20150302_1529'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gallery',
            name='Category',
        ),
        migrations.RemoveField(
            model_name='gallery',
            name='business',
        ),
        migrations.AlterUniqueTogether(
            name='galleryitem',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='galleryitem',
            name='Gallery',
        ),
        migrations.DeleteModel(
            name='Gallery',
        ),
        migrations.RemoveField(
            model_name='galleryitem',
            name='item',
        ),
        migrations.DeleteModel(
            name='GalleryItem',
        ),
        migrations.AlterField(
            model_name='event',
            name='EventType',
            field=models.IntegerField(default=0, choices=[(0, b'Follow User'), (1, b'Follow Tag'), (2, b'Shout Offer'), (3, b'Shout Request'), (4, b'Experience'), (5, b'Share Experience'), (6, b'Comment'), (7, b'Post Deal'), (8, b'Buy Deal'), (9, b'Follow Business')]),
            preserve_default=True,
        ),
    ]
