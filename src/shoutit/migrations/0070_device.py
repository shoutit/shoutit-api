# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

from django.db import migrations, models
from push_notifications.models import APNSDevice, GCMDevice

from common.constants import DEVICE_ANDROID, DEVICE_IOS
from shoutit.models import Device


def create_devices(apps, schema_editor):
    for apns in APNSDevice.objects.all():
        try:
            Device.objects.create(type=DEVICE_IOS, api_version='v2', push_device=apns)
        except:
            pass
    for gcm in GCMDevice.objects.all():
        try:
            Device.objects.create(type=DEVICE_ANDROID, api_version='v2', push_device=gcm)
        except:
            pass


class Migration(migrations.Migration):
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('shoutit', '0069_auto_20160329_1711'),
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('type', models.SmallIntegerField(db_index=True, choices=[(0, 'android'), (1, 'ios')])),
                ('api_version', models.CharField(max_length=10, db_index=True)),
                ('object_id', models.IntegerField(null=True, blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RunPython(create_devices)
    ]
