# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.contrib.postgres.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0022_shout_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkedFacebookPage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('facebook_id', models.CharField(max_length=24)),
                ('name', models.CharField(max_length=50)),
                ('access_token', models.CharField(max_length=512)),
                ('category', models.CharField(max_length=50)),
                ('perms', django.contrib.postgres.fields.ArrayField(default=list, size=None, base_field=models.CharField(max_length=25), blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='linkedfacebookaccount',
            name='name',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AddField(
            model_name='linkedfacebookpage',
            name='linked_facebook',
            field=models.ForeignKey(related_name='pages', to='shoutit.LinkedFacebookAccount'),
        ),
    ]
