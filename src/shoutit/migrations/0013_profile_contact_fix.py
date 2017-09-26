# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.contrib.postgres.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0012_profile_contact_init'),
    ]

    operations = [
        migrations.AlterField(
            model_name='linkedfacebookaccount',
            name='scopes',
            field=django.contrib.postgres.fields.ArrayField(default=['public_profile', 'email'], size=None, base_field=models.CharField(max_length=50), blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='profilecontact',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='profilecontact',
            name='hash',
        ),
    ]
