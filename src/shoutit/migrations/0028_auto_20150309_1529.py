# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0027_auto_20150305_1837'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='main_tag',
            field=models.OneToOneField(related_name='+', null=True, blank=True, to='shoutit.Tag'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='category',
            name='tags',
            field=models.ManyToManyField(related_name='category', null=True, to='shoutit.Tag', blank=True),
            preserve_default=True,
        ),
    ]
