# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.db import models, migrations

sql = [
    'CREATE EXTENSION "uuid-ossp";',
    'ALTER TABLE shoutit_stream_posts ALTER COLUMN id DROP DEFAULT;'
    'ALTER TABLE shoutit_stream_posts ALTER COLUMN id SET DATA TYPE UUID USING uuid_generate_v4();'
    'DROP EXTENSION "uuid-ossp";',
]

reverse_sql = [
    'ALTER TABLE shoutit_stream_posts DROP COLUMN id;',
    'ALTER TABLE shoutit_stream_posts ADD COLUMN id SERIAL;',
    'UPDATE shoutit_stream_posts SET id = DEFAULT;'
]


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit', '0043_fill_actions'),
    ]

    operations = [
        migrations.AddField(
            model_name='streampost',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True),
        ),
        migrations.AddField(
            model_name='streampost',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True),
        ),
        migrations.RunSQL(sql,
                          reverse_sql,
                          [migrations.AlterField(
                              model_name='streampost',
                              name='id',
                              field=models.UUIDField(default=uuid.uuid4, serialize=False, editable=False,
                                                     primary_key=True),
                          )]),
    ]
