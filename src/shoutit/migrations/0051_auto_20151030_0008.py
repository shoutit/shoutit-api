# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0050_discoveritem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='confirmtoken',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, 'Email Token'), (1, 'Number Token'), (2, 'Reset Password'), (3, 'Business Html Email Activate'), (4, 'Business Html Confirm')]),
        ),
    ]
