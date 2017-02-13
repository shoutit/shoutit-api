# -*- coding: utf-8 -*-
import uuid

import django.contrib.postgres.fields
import django.core.validators
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit', '0020_bookmark_like_shout'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageVerification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('status', models.PositiveSmallIntegerField(default=0, choices=[(0, 'Not submitted'), (1, 'Waiting'), (2, 'In review'), (3, 'Rejected'), (4, 'Accepted')])),
                ('business_name', models.CharField(max_length=50, validators=[django.core.validators.MinLengthValidator(2)])),
                ('business_email', models.EmailField(max_length=254)),
                ('contact_person', models.CharField(max_length=50, validators=[django.core.validators.MinLengthValidator(2)])),
                ('contact_number', models.CharField(max_length=20, validators=[django.core.validators.MinLengthValidator(8)])),
                ('images', django.contrib.postgres.fields.ArrayField(default=list, size=None, base_field=models.URLField(), blank=True)),
                ('admin', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='pageverification',
            name='page',
            field=models.OneToOneField(to='shoutit.Page', related_name='verification'),
        ),

        migrations.RenameField(
            model_name='page',
            old_name='is_claimed',
            new_name='is_verified',
        ),

        migrations.AlterField(
            model_name='page',
            name='is_verified',
            field=models.BooleanField(default=False, help_text='Designates whether the page is verified.',
                                      verbose_name='verified'),
        ),

    ]
