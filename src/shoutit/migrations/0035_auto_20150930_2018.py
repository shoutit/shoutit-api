# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
import re
import django.contrib.postgres.fields
from common.utils import process_tag
import shoutit.models.tag
import django.core.validators


def set_slugs(apps, schema_editor):
    categories = apps.get_model("shoutit", "Category").objects.all()
    for category in categories:
        category.slug = process_tag(category.name)
        category.save()


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0034_auto_20150906_1936'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shout',
            name='tags',
            field=django.contrib.postgres.fields.ArrayField(base_field=shoutit.models.tag.ShoutitSlugField(help_text='Required. 2 to 30 characters and can only contain a-z, 0-9, and the dash (-)', unique=True, max_length=30, db_index=True, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(re.compile('^[0-9a-z-]+$'), 'Enter a valid tag.', 'invalid')]), size=None),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=shoutit.models.tag.ShoutitSlugField(help_text='Required. 2 to 30 characters and can only contain a-z, 0-9, and the dash (-)', unique=True, max_length=30, db_index=True, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(re.compile('^[0-9a-z-]+$'), 'Enter a valid tag.', 'invalid')]),
        ),
        migrations.AddField(
            model_name='category',
            name='slug',
            field=shoutit.models.tag.ShoutitSlugField(max_length=30, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(re.compile('^[0-9a-z-]+$'), 'Enter a valid tag.', 'invalid')], help_text='Required. 2 to 30 characters and can only contain a-z, 0-9, and the dash (-)', unique=False, db_index=False, null=True),
            preserve_default=False,
        ),
        migrations.RunPython(set_slugs),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=shoutit.models.tag.ShoutitSlugField(help_text='Required. 2 to 30 characters and can only contain a-z, 0-9, and the dash (-)', unique=True, max_length=30, db_index=True, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(re.compile('^[0-9a-z-]+$'), 'Enter a valid tag.', 'invalid')]),
        ),
    ]
