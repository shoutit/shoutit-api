# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0027_date_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='language',
            field=models.CharField(default='en-us', max_length=7, verbose_name='accepted language'),
        ),
    ]
