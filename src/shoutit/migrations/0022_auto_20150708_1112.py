# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0021_auto_20150706_0921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='currency',
            field=models.ForeignKey(blank=True, to='shoutit.Currency', null=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='description',
            field=models.TextField(max_length=2000),
        ),
        migrations.AlterField(
            model_name='item',
            name='name',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='item',
            name='price',
            field=models.FloatField(default=0, null=True, blank=True),
        ),
    ]
