# -*- coding: utf-8 -*-
from django.db import migrations, models
from django.conf import settings
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('shoutit_credit', '0004_auto_20160614_0058'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvitationCode',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('code', models.CharField(unique=True, max_length=10)),
                ('used_count', models.SmallIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(related_name='invitation_codes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
