# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shoutit.models.tag


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0065_add_is_indexed'),
    ]

    operations = [
        migrations.AddField(
            model_name='tagkey',
            name='category',
            field=models.ForeignKey(related_name='tag_keys', default=None, to='shoutit.Category'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='tagkey',
            name='key',
            field=shoutit.models.tag.ShoutitSlugField(help_text='Required. 1 to 30 characters and can only contain small letters, numbers, underscores or hyphens.'),
        ),
        migrations.AlterField(
            model_name='tagkey',
            name='values_type',
            field=models.PositiveSmallIntegerField(default=1, choices=[(0, 'int'), (1, 'str')]),
        ),
        migrations.AlterUniqueTogether(
            name='tagkey',
            unique_together=set([('key', 'category')]),
        ),
    ]
