# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_pgjson.fields
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('transaction_type', models.SmallIntegerField(choices=[(0, 'in'), (1, 'out')])),
                ('type', models.CharField(max_length=30)),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=250)),
                ('options', django_pgjson.fields.JsonField(default=dict, blank=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CreditTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('amount', models.IntegerField()),
                ('properties', django_pgjson.fields.JsonField(default=dict, blank=True)),
                ('rule', models.ForeignKey(related_name='transactions', to='shoutit_credit.CreditRule')),
                ('user', models.ForeignKey(related_name='credit_transactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PromoteLabel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=250)),
                ('color', models.CharField(max_length=9)),
                ('bg_color', models.CharField(max_length=9)),
                ('rank', models.PositiveSmallIntegerField()),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
