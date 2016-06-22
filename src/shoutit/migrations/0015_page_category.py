# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mptt.fields
from django.db import migrations, models

from common.constants import USER_TYPE_PAGE
from shoutit.models import User, PageCategory


def fill_data(apps, schema_editor):
    # Remove previous pages
    User.objects.filter(type=USER_TYPE_PAGE).delete()
    # Remove previous page categories
    PageCategory.objects.all().delete()

    # Main categories
    c1 = PageCategory.objects.create(name='Local Business', slug='main-local-business')
    c2 = PageCategory.objects.create(name='Company', slug='main-company')
    c3 = PageCategory.objects.create(name='Brand or Product', slug='main-brand_product')
    c4 = PageCategory.objects.create(name='Community', slug='main-community')

    # Sub categories
    PageCategory.objects.create(name='Local Business', slug='local-business', parent=c1)
    PageCategory.objects.create(name='Company', slug='company', parent=c2)
    PageCategory.objects.create(name='Brand or Product', slug='brand_product', parent=c3)
    PageCategory.objects.create(name='Community', slug='community', parent=c4)


def remove_data(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit', '0014_user_on_mp_people'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pagecategory',
            name='name',
            field=models.CharField(max_length=100, db_index=True),
        ),
        migrations.AddField(
            model_name='pagecategory',
            name='image',
            field=models.URLField(default='', blank=True),
        ),
        migrations.AddField(
            model_name='pagecategory',
            name='level',
            field=models.PositiveIntegerField(default=0, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pagecategory',
            name='lft',
            field=models.PositiveIntegerField(default=0, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pagecategory',
            name='rght',
            field=models.PositiveIntegerField(default=0, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pagecategory',
            name='tree_id',
            field=models.PositiveIntegerField(default=0, editable=False, db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='pagecategory',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='children', blank=True, to='shoutit.PageCategory', null=True),
        ),
        migrations.RunPython(fill_data, remove_data)
    ]
