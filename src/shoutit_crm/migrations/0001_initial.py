# -*- coding: utf-8 -*-
from django.db import migrations, models
import django_pgjson.fields
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CRMProvider',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='XMLCRMShout',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('object_id', models.UUIDField(null=True, blank=True)),
                ('id_on_source', models.CharField(max_length=100)),
                ('xml_data', models.TextField()),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('shout', models.ForeignKey(related_name='crm_shout', to='shoutit.Shout')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='XMLLinkCRMSource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('type', models.PositiveSmallIntegerField(choices=[(0, 'XML Link')])),
                ('status', models.PositiveSmallIntegerField(choices=[(0, 'Disabled'), (1, 'Waiting Approval'), (2, 'Fetching'), (3, 'Enabled'), (4, 'Blocked')])),
                ('url', models.URLField()),
                ('mapping', django_pgjson.fields.JsonField()),
                ('provider', models.ForeignKey(related_name='xmllinkcrmsource_set', to='shoutit_crm.CRMProvider')),
                ('user', models.ForeignKey(related_name='xmllinkcrmsource_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='xmlcrmshout',
            unique_together=set([('content_type', 'object_id', 'id_on_source')]),
        ),
    ]
