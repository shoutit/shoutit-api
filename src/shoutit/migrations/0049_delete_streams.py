# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0048_listen2'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='listen',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='listen',
            name='page_admin_user',
        ),
        migrations.RemoveField(
            model_name='listen',
            name='stream',
        ),
        migrations.RemoveField(
            model_name='listen',
            name='user',
        ),
        migrations.AlterUniqueTogether(
            name='stream',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='stream',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='stream',
            name='listeners',
        ),
        migrations.RemoveField(
            model_name='stream',
            name='posts',
        ),
        migrations.RemoveField(
            model_name='streampost',
            name='post',
        ),
        migrations.RemoveField(
            model_name='streampost',
            name='stream',
        ),
        migrations.DeleteModel(
            name='Listen',
        ),
        migrations.DeleteModel(
            name='Stream',
        ),
        migrations.DeleteModel(
            name='StreamPost',
        ),
    ]
