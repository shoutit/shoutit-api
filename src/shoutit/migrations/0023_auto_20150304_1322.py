# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import uuidfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0022_auto_20150302_2301'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeaturedTag',
            fields=[
                ('id', uuidfield.fields.UUIDField(primary_key=True, serialize=False, editable=False, max_length=32, blank=True, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('country', models.CharField(default=b'AE', max_length=200, db_index=True)),
                ('city', models.CharField(default=b'Dubai', max_length=200, db_index=True)),
                ('rank', models.PositiveSmallIntegerField()),
                ('tag', models.ForeignKey(related_name='featured_in', to='shoutit.Tag')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='featuredtag',
            unique_together=set([('tag', 'country', 'city', 'rank')]),
        ),
    ]
