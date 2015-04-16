# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0003_auto_20150416_0039'),
    ]

    operations = [
        migrations.RenameField(
            model_name='report',
            old_name='IsSolved',
            new_name='is_solved',
        ),
        migrations.RemoveField(
            model_name='report',
            name='DateCreated',
        ),
        migrations.AddField(
            model_name='report',
            name='type',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='report',
            name='user',
            field=models.ForeignKey(related_name='reports', to=settings.AUTH_USER_MODEL),
        ),
    ]
