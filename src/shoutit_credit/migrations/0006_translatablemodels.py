# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_credit', '0005_invitationcode'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditRuleTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_local_name', models.CharField(default='', max_length=50, blank=True)),
                ('language_code', models.CharField(max_length=15, db_index=True)),
                ('master', models.ForeignKey(related_name='translations', editable=False, to='shoutit_credit.CreditRule', null=True)),
            ],
            options={
                'managed': True,
                'abstract': False,
                'db_table': 'shoutit_credit_creditrule_translation',
                'db_tablespace': '',
                'default_permissions': (),
            },
        ),
        migrations.CreateModel(
            name='PromoteLabelTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('_local_name', models.CharField(default='', max_length=50, blank=True)),
                ('_local_description', models.CharField(default='', max_length=250, blank=True)),
                ('language_code', models.CharField(max_length=15, db_index=True)),
                ('master', models.ForeignKey(related_name='translations', editable=False, to='shoutit_credit.PromoteLabel', null=True)),
            ],
            options={
                'managed': True,
                'abstract': False,
                'db_table': 'shoutit_credit_promotelabel_translation',
                'db_tablespace': '',
                'default_permissions': (),
            },
        ),
        migrations.AlterUniqueTogether(
            name='promotelabeltranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='creditruletranslation',
            unique_together=set([('language_code', 'master')]),
        ),
    ]
