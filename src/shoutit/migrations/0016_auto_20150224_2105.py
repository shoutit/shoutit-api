# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0015_auto_20150224_1934'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message2',
            name='message',
            field=models.CharField(help_text='The text body of this message, could be None if the message has attachments', max_length=2000, null=True, blank=True),
            preserve_default=True,
        ),
    ]
