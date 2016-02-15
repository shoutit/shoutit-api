# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0058_new_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='icon',
            field=models.URLField(default='', max_length=1024, blank=True),
        ),
    ]
