# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0002_default_object_id_bug_fix'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='followship',
            name='follower',
        ),
        migrations.RemoveField(
            model_name='followship',
            name='stream',
        ),
        migrations.RemoveField(
            model_name='shoutwrap',
            name='Stream',
        ),
        migrations.RemoveField(
            model_name='shoutwrap',
            name='shout',
        ),
        migrations.RemoveField(
            model_name='business',
            name='Stream',
        ),
        migrations.RemoveField(
            model_name='post',
            name='Streams',
        ),
        migrations.RemoveField(
            model_name='post',
            name='streams2_ids',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='Following',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='Interests',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='Stream',
        ),
        migrations.RemoveField(
            model_name='tag',
            name='Stream',
        ),
        migrations.RemoveField(
            model_name='trade',
            name='MaxDistance',
        ),
        migrations.RemoveField(
            model_name='trade',
            name='MaxFollowings',
        ),
        migrations.RemoveField(
            model_name='trade',
            name='MaxPrice',
        ),
        migrations.RemoveField(
            model_name='trade',
            name='StreamsCode',
        ),
        migrations.RemoveField(
            model_name='trade',
            name='base_date_published',
        ),
        migrations.RemoveField(
            model_name='trade',
            name='recommended_stream',
        ),
        migrations.RemoveField(
            model_name='trade',
            name='related_stream',
        ),
        migrations.DeleteModel(
            name='FollowShip',
        ),
        migrations.DeleteModel(
            name='ShoutWrap',
        ),
        migrations.DeleteModel(
            name='Stream',
        ),
    ]
