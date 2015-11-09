# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.postgres.fields
import shoutit.models.tag
import django.contrib.postgres.fields.hstore
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0051_auto_20151030_0008'),
    ]

    operations = [
        migrations.CreateModel(
            name='TagKey',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('key', shoutit.models.tag.ShoutitSlugField(help_text='Required. 1 to 30 characters and can only contain small letters, numbers, underscores or hyphens.', unique=True)),
                ('values_type', models.PositiveSmallIntegerField(choices=[(0, 'int'), (1, 'str')])),
                ('definition', models.CharField(default='', max_length=100, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='category',
            name='filters',
            field=django.contrib.postgres.fields.ArrayField(default=list, size=10, base_field=shoutit.models.tag.ShoutitSlugField(help_text='Required. 1 to 30 characters and can only contain small letters, numbers, underscores or hyphens.'), blank=True),
        ),
        migrations.AddField(
            model_name='shout',
            name='tags2',
            field=django.contrib.postgres.fields.hstore.HStoreField(default=dict, blank=True),
        ),
        migrations.AddField(
            model_name='tag',
            name='key',
            field=shoutit.models.tag.ShoutitSlugField(default='', help_text='Required. 1 to 30 characters and can only contain small letters, numbers, underscores or hyphens.', blank=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=shoutit.models.tag.ShoutitSlugField(help_text='Required. 1 to 30 characters and can only contain small letters, numbers, underscores or hyphens.', unique=True),
        ),
        migrations.AlterField(
            model_name='pagecategory',
            name='slug',
            field=shoutit.models.tag.ShoutitSlugField(help_text='Required. 1 to 30 characters and can only contain small letters, numbers, underscores or hyphens.', unique=True),
        ),
        migrations.AlterField(
            model_name='shout',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(base_field=shoutit.models.tag.ShoutitSlugField(help_text='Required. 1 to 30 characters and can only contain small letters, numbers, underscores or hyphens.'), size=None),
        ),
        migrations.AlterField(
            model_name='tag',
            name='definition',
            field=models.TextField(default='New Tag!', max_length=512, blank=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=shoutit.models.tag.ShoutitSlugField(help_text='Required. 1 to 30 characters and can only contain small letters, numbers, underscores or hyphens.'),
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('name', 'key')]),
        ),
    ]
