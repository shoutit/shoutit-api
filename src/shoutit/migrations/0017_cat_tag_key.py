# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shoutit


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit', '0016_translatablemodels'),
    ]

    operations = [
        # Category
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(unique=True, max_length=30),
        ),

        # TagKey
        migrations.AddField(
            model_name='tagkey',
            name='name',
            field=models.CharField(default='', max_length=30, db_index=True),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='tagkey',
            old_name='key',
            new_name='slug',
        ),
        migrations.AlterUniqueTogether(
            name='tagkey',
            unique_together=set([('slug', 'category')]),
        ),

        # Tag
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([]),
        ),
        migrations.RemoveField(model_name='tag', name='key'),

        migrations.AddField(
            model_name='tag',
            name='slug',
            field=shoutit.models.tag.ShoutitSlugField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tag',
            name='key',
            field=models.ForeignKey(related_name='tags', blank=True, to='shoutit.TagKey', null=True),
        ),
        migrations.AddField(
            model_name='tag',
            name='name2',
            field=models.CharField(default='', max_length=30, db_index=True),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='tag',
            unique_together=set([('slug', 'key')]),
        ),
    ]
