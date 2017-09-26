# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.contrib.postgres.fields
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0011_fb_friends'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileContact',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('emails', django.contrib.postgres.fields.ArrayField(default=list, size=None, base_field=models.EmailField(max_length=254, verbose_name='email address', blank=True), blank=True)),
                ('mobiles', django.contrib.postgres.fields.ArrayField(default=list, size=None, base_field=models.CharField(max_length=20, verbose_name='mobile', blank=True), blank=True)),
                ('hash', models.CharField(max_length=1000)),
                ('user', models.ForeignKey(related_name='contacts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='linkedfacebookaccount',
            name='facebook_id',
            field=models.CharField(unique=True, max_length=24),
        ),
        migrations.AlterField(
            model_name='linkedgoogleaccount',
            name='gplus_id',
            field=models.CharField(unique=True, max_length=64),
        ),
        migrations.AlterUniqueTogether(
            name='profilecontact',
            unique_together=set([('user', 'hash')]),
        ),
    ]
