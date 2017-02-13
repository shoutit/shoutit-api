# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0018_tag_name_fill'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='tagkey',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='tagkey',
            name='category',
        ),
        migrations.AlterField(
            model_name='category',
            name='main_tag',
            field=models.OneToOneField(null=True, blank=True, to='shoutit.Tag'),
        ),
        migrations.RemoveField(
            model_name='category',
            name='filters',
        ),
        migrations.RemoveField(
            model_name='category',
            name='tags',
        ),
        migrations.AddField(
            model_name='category',
            name='filters',
            field=models.ManyToManyField(related_name='categories', to='shoutit.TagKey', blank=True),
        ),
    ]
