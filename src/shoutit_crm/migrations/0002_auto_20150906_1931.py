# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_crm', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='xmlcrmshout',
            name='shout',
            field=models.ForeignKey(related_name='crm_shout', to='shoutit.Shout'),
        ),
    ]
