# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_crm', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crmprovider',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='crmprovider',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='xmlcrmshout',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='xmlcrmshout',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='xmllinkcrmsource',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='xmllinkcrmsource',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
    ]
