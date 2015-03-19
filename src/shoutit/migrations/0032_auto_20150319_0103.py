# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0031_auto_20150319_0019'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dbuser',
            name='db_link',
            field=models.URLField(max_length=1000),
            preserve_default=True,
        ),
    ]
