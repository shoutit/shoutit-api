# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_pusher', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pusherchannel',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pusherchannel',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pusherchanneljoin',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pusherchanneljoin',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pusherdevice',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='pusherdevice',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
    ]
