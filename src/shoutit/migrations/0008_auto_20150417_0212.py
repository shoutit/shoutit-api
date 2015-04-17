# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0007_auto_20150417_0212'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='videos',
            field=models.ManyToManyField(to='shoutit.Video'),
        ),
    ]
