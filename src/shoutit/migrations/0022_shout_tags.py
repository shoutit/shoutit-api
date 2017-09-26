# -*- coding: utf-8 -*-
from django.db import migrations, models
import shoutit.models.tag


def remove_tags(apps, schema_editor):
    # This deleted all tags that are not used as the `main_tag` of any category
    Tag = apps.get_model('shoutit', 'Tag')
    Tag.objects.filter(category=None).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0021_page_verification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shout',
            name='filters',
        ),
        migrations.RemoveField(
            model_name='shout',
            name='tags',
        ),
        migrations.RunPython(remove_tags),
        migrations.AlterField(
            model_name='tagkey',
            name='slug',
            field=shoutit.models.tag.ShoutitSlugField(unique=True),
        ),
        migrations.AddField(
            model_name='shout',
            name='tags',
            field=models.ManyToManyField(related_name='shouts', to='shoutit.Tag', blank=True),
        ),

    ]
