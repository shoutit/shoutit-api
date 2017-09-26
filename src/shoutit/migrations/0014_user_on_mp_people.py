# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0013_profile_contact_fix'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='on_mp_people',
            field=models.BooleanField(default=False, help_text='Designates whether this user is on MixPanel People.', verbose_name='mixpanel people status'),
        ),
    ]
