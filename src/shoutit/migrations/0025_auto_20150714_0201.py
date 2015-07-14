# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0024_profile_mobile'),
    ]

    operations = [
        migrations.AddField(
            model_name='cluser',
            name='converted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='cluser',
            name='converted_at',
            field=models.DateTimeField(null=True, verbose_name='Conversion time'),
        ),
        migrations.AddField(
            model_name='dbuser',
            name='converted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dbuser',
            name='converted_at',
            field=models.DateTimeField(null=True, verbose_name='Conversion time'),
        ),
        migrations.AddField(
            model_name='dbz2user',
            name='converted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dbz2user',
            name='converted_at',
            field=models.DateTimeField(null=True, verbose_name='Conversion time'),
        ),
    ]
