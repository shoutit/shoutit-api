# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0072_remove_v1'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shout',
            name='item',
            field=models.OneToOneField(to='shoutit.Item'),
        ),
    ]
