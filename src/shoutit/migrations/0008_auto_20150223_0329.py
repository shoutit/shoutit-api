# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0007_auto_20150222_2036'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='business',
            name='name',
        ),
        migrations.AlterField(
            model_name='storedimage',
            name='item',
            field=models.ForeignKey(related_name='images', blank=True, to='shoutit.Item', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='storedimage',
            name='shout',
            field=models.ForeignKey(related_name='images', blank=True, to='shoutit.Shout', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='trade',
            name='item',
            field=models.OneToOneField(related_name='shout', null=True, blank=True, to='shoutit.Item'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='trade',
            name='recommended_stream',
            field=models.OneToOneField(related_name='init_shout_recommended', null=True, blank=True, to='shoutit.Stream'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='trade',
            name='related_stream',
            field=models.OneToOneField(related_name='init_shout_related', null=True, blank=True, to='shoutit.Stream'),
            preserve_default=True,
        ),
    ]
