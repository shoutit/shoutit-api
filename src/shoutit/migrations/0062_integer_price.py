# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from shoutit.models import Item

# Round to two digits and convert to cents
ALTER_SQL = "ALTER TABLE shoutit_item ALTER COLUMN price TYPE bigint USING ((round(price::numeric,2)*100)::bigint);"


def fix_prices(apps, schema_editor):
    Item.objects.filter(price__gte=models.BigIntegerField.MAX_BIGINT).update(price=0)


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit', '0061_user_is_guest'),
    ]

    operations = [
        migrations.RunPython(fix_prices),
        migrations.RunSQL(ALTER_SQL, None, [
            migrations.AlterField(
                model_name='item',
                name='price',
                field=models.BigIntegerField(null=True, blank=True),
            ),
        ]),
    ]
