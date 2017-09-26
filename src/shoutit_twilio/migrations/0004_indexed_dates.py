# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_twilio', '0003_set_new_ttl'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoclient',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='videoclient',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
    ]
