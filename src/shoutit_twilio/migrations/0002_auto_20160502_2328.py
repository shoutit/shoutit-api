# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_twilio', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoclient',
            name='ttl',
            field=models.IntegerField(default=86400),
        ),
    ]
