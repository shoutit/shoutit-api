# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0013_conversation2_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messageattachment',
            name='conversation',
            field=models.ForeignKey(related_name='messages_attachments', to='shoutit.Conversation2'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='messageattachment',
            name='message',
            field=models.ForeignKey(related_name='attachments', to='shoutit.Message2'),
            preserve_default=True,
        ),
    ]
