# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0004_auto_20160510_0834'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messageattachment',
            name='type',
            field=models.SmallIntegerField(choices=[(0, 'shout'), (1, 'location'), (2, 'media'), (3, 'profile')]),
        ),
    ]
