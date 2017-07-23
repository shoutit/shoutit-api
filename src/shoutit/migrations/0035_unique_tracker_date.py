# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0034_tracker_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trackerdata',
            name='date',
            field=models.DateField(unique=True),
        ),
    ]
