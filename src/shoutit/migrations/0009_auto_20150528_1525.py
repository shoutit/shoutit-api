# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0008_auto_20150516_1333'),
    ]

    operations = [
        migrations.RenameField(
            model_name='tag',
            old_name='Creator',
            new_name='creator',
        ),
        migrations.RenameField(
            model_name='tag',
            old_name='Definition',
            new_name='definition',
        ),
        migrations.RemoveField(
            model_name='tag',
            name='Parent',
        ),
        migrations.AlterField(
            model_name='tag',
            name='image',
            field=models.URLField(default='https://tag-image.static.shoutit.com/default.jpg', max_length=1024, blank=True),
        ),
    ]
