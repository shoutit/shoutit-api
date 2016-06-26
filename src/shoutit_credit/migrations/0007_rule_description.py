# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_credit', '0006_translatablemodels'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditruletranslation',
            name='_local_description',
            field=models.CharField(default='', max_length=250, blank=True),
        ),
    ]
