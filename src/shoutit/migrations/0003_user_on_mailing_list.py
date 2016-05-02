# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0002_initial_data'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='on_mailing_list',
            field=models.BooleanField(default=False, help_text='Designates whether this user is on the main mailing list.', verbose_name='mailing list status'),
        ),
    ]
