# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0003_auto_20150417_0131'),
    ]

    operations = [
        migrations.RenameField(
            model_name='item',
            old_name='Currency',
            new_name='currency',
        ),
        migrations.RenameField(
            model_name='item',
            old_name='Description',
            new_name='description',
        ),
        migrations.RenameField(
            model_name='item',
            old_name='Price',
            new_name='price',
        ),
        migrations.RenameField(
            model_name='payment',
            old_name='Currency',
            new_name='currency',
        ),
        migrations.RenameField(
            model_name='service',
            old_name='Price',
            new_name='price',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='DateCreated',
        ),
        migrations.RemoveField(
            model_name='confirmtoken',
            name='DateCreated',
        ),
        migrations.RemoveField(
            model_name='item',
            name='DateCreated',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='DateCreated',
        ),
        migrations.RemoveField(
            model_name='payment',
            name='DateUpdated',
        ),
        migrations.RemoveField(
            model_name='sharedexperience',
            name='DateCreated',
        ),
        migrations.RemoveField(
            model_name='tag',
            name='DateCreated',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='DateCreated',
        ),
        migrations.RemoveField(
            model_name='transaction',
            name='DateUpdated',
        ),
    ]
