# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_credit', '0007_rule_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='creditrule',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='creditrule',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='credittransaction',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='credittransaction',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='invitationcode',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='invitationcode',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='promotelabel',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='promotelabel',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
        migrations.AlterField(
            model_name='shoutpromotion',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Creation time', db_index=True),
        ),
        migrations.AlterField(
            model_name='shoutpromotion',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Modification time', db_index=True),
        ),
    ]
