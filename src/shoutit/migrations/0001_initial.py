# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import re
import django.utils.timezone
import django.contrib.auth.models
import django.db.models.deletion
import shoutit.models.base
from django.conf import settings
import django.core.validators
import common.utils
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('username', models.CharField(help_text='Required. 2 to 30 characters and can only contain A-Z, a-z, 0-9, and periods (.)', unique=True, max_length=30, verbose_name='username', validators=[django.core.validators.RegexValidator(re.compile('[0-9a-zA-Z.]{2,30}'), 'Enter a valid username.', 'invalid'), django.core.validators.MinLengthValidator(2), common.utils.AllowedUsernamesValidator()])),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name', validators=[django.core.validators.MinLengthValidator(2)])),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='last name', validators=[django.core.validators.MinLengthValidator(2)])),
                ('email', models.EmailField(max_length=254, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            bases=(models.Model, shoutit.models.base.APIModelMixin),
            managers=[
                (b'objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Business',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('image', models.CharField(max_length=1024, null=True, blank=True)),
                ('About', models.TextField(default='', max_length=512, null=True, blank=True)),
                ('Phone', models.CharField(max_length=20, unique=True, null=True, blank=True)),
                ('Website', models.URLField(max_length=1024, null=True, blank=True)),
                ('country', models.CharField(db_index=True, max_length=2, null=True, blank=True)),
                ('city', models.CharField(db_index=True, max_length=200, null=True, blank=True)),
                ('latitude', models.FloatField(default=0.0)),
                ('longitude', models.FloatField(default=0.0)),
                ('address', models.CharField(db_index=True, max_length=200, null=True, blank=True)),
                ('Confirmed', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BusinessCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('name', models.CharField(max_length=1024, db_index=True)),
                ('Source', models.IntegerField(default=0)),
                ('SourceID', models.CharField(max_length=128, blank=True)),
                ('Parent', models.ForeignKey(related_name='children', default=None, blank=True, to='shoutit.BusinessCategory', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BusinessConfirmation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('DateSent', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BusinessCreateApplication',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('name', models.CharField(db_index=True, max_length=1024, null=True, blank=True)),
                ('image', models.CharField(max_length=1024, null=True, blank=True)),
                ('About', models.TextField(default='', max_length=512, null=True, blank=True)),
                ('Phone', models.CharField(max_length=20, null=True, blank=True)),
                ('Website', models.URLField(max_length=1024, null=True, blank=True)),
                ('longitude', models.FloatField(default=0.0)),
                ('latitude', models.FloatField(default=0.0)),
                ('country', models.CharField(db_index=True, max_length=2, null=True, blank=True)),
                ('city', models.CharField(db_index=True, max_length=200, null=True, blank=True)),
                ('address', models.CharField(db_index=True, max_length=200, null=True, blank=True)),
                ('DateApplied', models.DateField(auto_now_add=True)),
                ('Status', models.IntegerField(default=0, db_index=True)),
                ('Category', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='shoutit.BusinessCategory', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='BusinessSource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('Source', models.IntegerField(default=0)),
                ('SourceID', models.CharField(max_length=128, blank=True)),
                ('business', models.OneToOneField(related_name='Source', to='shoutit.Business')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('name', models.CharField(unique=True, max_length=100, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CLUser',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('cl_email', models.EmailField(max_length=254)),
                ('user', models.OneToOneField(related_name='cluser', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('is_disabled', models.BooleanField(default=False)),
                ('text', models.TextField(max_length=300)),
                ('DateCreated', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ConfirmToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('Token', models.CharField(unique=True, max_length=24, db_index=True)),
                ('type', models.IntegerField(default=0)),
                ('DateCreated', models.DateField(auto_now_add=True)),
                ('Email', models.CharField(max_length=128, null=True, blank=True)),
                ('is_disabled', models.BooleanField(default=False)),
                ('user', models.ForeignKey(related_name='Tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('is_read', models.BooleanField(default=False)),
                ('VisibleToRecivier', models.BooleanField(default=True)),
                ('VisibleToSender', models.BooleanField(default=True)),
                ('FromUser', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
                ('ToUser', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Conversation2',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('object_id', models.UUIDField(null=True, blank=True)),
                ('type', models.SmallIntegerField(choices=[(0, 'chat'), (1, 'about_shout')])),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, shoutit.models.base.APIModelMixin),
        ),
        migrations.CreateModel(
            name='Conversation2Delete',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('conversation', models.ForeignKey(related_name='deleted_set', to='shoutit.Conversation2')),
                ('user', models.ForeignKey(related_name='deleted_conversations2_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('code', models.CharField(max_length=10)),
                ('country', models.CharField(max_length=10, blank=True)),
                ('name', models.CharField(max_length=64, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DBCLConversation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('in_email', models.EmailField(max_length=254, null=True, blank=True)),
                ('ref', models.CharField(max_length=100, null=True, blank=True)),
                ('from_user', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
                ('to_user', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DBUser',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('db_link', models.URLField(max_length=1000)),
                ('user', models.OneToOneField(related_name='dbuser', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DealBuy',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('Amount', models.IntegerField(default=1)),
                ('DateBought', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name='DealsBought', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FbContest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('ContestId', models.IntegerField(db_index=True)),
                ('FbId', models.CharField(max_length=24, db_index=True)),
                ('ShareId', models.CharField(default=None, max_length=50, null=True, blank=True)),
                ('user', models.ForeignKey(related_name='Contest_1', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FeaturedTag',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('country', models.CharField(default='AE', max_length=200, db_index=True)),
                ('city', models.CharField(default='Dubai', max_length=200, db_index=True)),
                ('rank', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('name', models.CharField(default='', max_length=512, blank=True)),
                ('Description', models.CharField(max_length=1000)),
                ('Price', models.FloatField(default=0.0)),
                ('State', models.IntegerField(default=0, db_index=True)),
                ('DateCreated', models.DateTimeField(auto_now_add=True)),
                ('Currency', models.ForeignKey(related_name='Items', to='shoutit.Currency')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LinkedFacebookAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('facebook_id', models.CharField(max_length=24, db_index=True)),
                ('AccessToken', models.CharField(max_length=512)),
                ('ExpiresIn', models.BigIntegerField(default=0)),
                ('user', models.OneToOneField(related_name='linked_facebook', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LinkedGoogleAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('credentials_json', models.CharField(max_length=4096)),
                ('gplus_id', models.CharField(max_length=64, db_index=True)),
                ('user', models.OneToOneField(related_name='linked_gplus', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Listen',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('date_listened', models.DateTimeField(auto_now_add=True)),
                ('listener', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('text', models.TextField(null=True, blank=True)),
                ('is_read', models.BooleanField(default=False)),
                ('VisibleToRecivier', models.BooleanField(default=True)),
                ('VisibleToSender', models.BooleanField(default=True)),
                ('DateCreated', models.DateTimeField(auto_now_add=True)),
                ('Conversation', models.ForeignKey(related_name='Messages', to='shoutit.Conversation')),
                ('FromUser', models.ForeignKey(related_name='received_messages', to=settings.AUTH_USER_MODEL)),
                ('ToUser', models.ForeignKey(related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Message2',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('text', models.CharField(help_text='The text body of this message, could be None if the message has attachments', max_length=2000, null=True, blank=True)),
                ('conversation', models.ForeignKey(related_name='messages2', to='shoutit.Conversation2')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Message2Delete',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('conversation', models.ForeignKey(related_name='messages2_deleted_set', to='shoutit.Conversation2')),
                ('message', models.ForeignKey(related_name='deleted_set', to='shoutit.Message2')),
                ('user', models.ForeignKey(related_name='deleted_messages2_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Message2Read',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('conversation', models.ForeignKey(related_name='messages2_read_set', to='shoutit.Conversation2')),
                ('message', models.ForeignKey(related_name='read_set', to='shoutit.Message2')),
                ('user', models.ForeignKey(related_name='read_messages2_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MessageAttachment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('object_id', models.UUIDField(null=True, blank=True)),
                ('type', models.SmallIntegerField(choices=[(0, 'shout'), (1, 'location')])),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('conversation', models.ForeignKey(related_name='messages_attachments', to='shoutit.Conversation2')),
                ('message', models.ForeignKey(related_name='attachments', to='shoutit.Message2')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('object_id', models.UUIDField(null=True, blank=True)),
                ('type', models.IntegerField(default=0, choices=[(0, 'listen'), (1, 'message'), (2, 'Experience'), (3, 'Experience Shared'), (4, 'Comment')])),
                ('is_read', models.BooleanField(default=False)),
                ('FromUser', models.ForeignKey(related_name='+', default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('ToUser', models.ForeignKey(related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('object_id', models.UUIDField(null=True, blank=True)),
                ('DateCreated', models.DateTimeField(auto_now_add=True)),
                ('DateUpdated', models.DateTimeField(auto_now=True)),
                ('Amount', models.FloatField()),
                ('Status', models.IntegerField()),
                ('Currency', models.ForeignKey(related_name='+', to='shoutit.Currency')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('name', models.CharField(unique=True, max_length=512, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('text', models.TextField(default='', max_length=2000, db_index=True, blank=True)),
                ('type', models.IntegerField(default=0, db_index=True, choices=[(0, 'request'), (1, 'offer'), (2, 'Experience'), (3, 'Deal'), (4, 'Event')])),
                ('date_published', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('muted', models.BooleanField(default=False, db_index=True)),
                ('is_disabled', models.BooleanField(default=False, db_index=True)),
                ('country', models.CharField(db_index=True, max_length=2, null=True, blank=True)),
                ('city', models.CharField(db_index=True, max_length=200, null=True, blank=True)),
                ('latitude', models.FloatField(default=0.0)),
                ('longitude', models.FloatField(default=0.0)),
                ('address', models.CharField(db_index=True, max_length=200, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, shoutit.models.base.APIModelMixin),
        ),
        migrations.CreateModel(
            name='PredefinedCity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('city', models.CharField(default='', unique=True, max_length=200, db_index=True, blank=True)),
                ('city_encoded', models.CharField(default='', unique=True, max_length=200, db_index=True, blank=True)),
                ('country', models.CharField(default='', max_length=2, db_index=True, blank=True)),
                ('latitude', models.FloatField(default=0.0)),
                ('longitude', models.FloatField(default=0.0)),
                ('Approved', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('image', models.CharField(max_length=1024, null=True, blank=True)),
                ('country', models.CharField(default='AE', max_length=200, db_index=True)),
                ('city', models.CharField(default='Dubai', max_length=200, db_index=True)),
                ('latitude', models.FloatField(default=25.1993957)),
                ('longitude', models.FloatField(default=55.2738326)),
                ('Bio', models.TextField(default=b'New Shouter!', max_length=512, null=True, blank=True)),
                ('Mobile', models.CharField(max_length=20, unique=True, null=True, blank=True)),
                ('birthday', models.DateField(null=True, blank=True)),
                ('Sex', models.NullBooleanField()),
                ('isSSS', models.BooleanField(default=False, db_index=True)),
                ('LastToken', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='shoutit.ConfirmToken', null=True)),
                ('user', models.OneToOneField(related_name='profile', null=True, blank=True, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('object_id', models.UUIDField(null=True, blank=True)),
                ('text', models.TextField(max_length=300, null=True, blank=True)),
                ('type', models.IntegerField(default=0, choices=[(0, 'general'), (1, 'web_app'), (2, 'iphone_app'), (3, 'android_app'), (4, 'user'), (5, 'shout'), (6, 'business'), (7, 'item'), (8, 'experience'), (9, 'comment')])),
                ('is_solved', models.BooleanField(default=False)),
                ('is_disabled', models.BooleanField(default=False)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('user', models.ForeignKey(related_name='reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('code', models.CharField(max_length=256)),
                ('name', models.CharField(max_length=1024)),
                ('Price', models.FloatField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServiceBuy',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('Amount', models.IntegerField(default=1)),
                ('DateBought', models.DateTimeField(auto_now_add=True)),
                ('Service', models.ForeignKey(related_name='Buyers', to='shoutit.Service')),
                ('user', models.ForeignKey(related_name='Services', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ServiceUsage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('Amount', models.IntegerField(default=1)),
                ('DateUsed', models.DateTimeField(auto_now_add=True)),
                ('Service', models.ForeignKey(related_name='BuyersUsages', to='shoutit.Service')),
                ('user', models.ForeignKey(related_name='ServicesUsages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SharedExperience',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('DateCreated', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name='SharedExperiences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SharedLocation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('latitude', models.FloatField(validators=[django.core.validators.MaxValueValidator(90), django.core.validators.MinValueValidator(-90)])),
                ('longitude', models.FloatField(validators=[django.core.validators.MaxValueValidator(180), django.core.validators.MinValueValidator(-180)])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StoredFile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('File', models.CharField(max_length=1024)),
                ('type', models.IntegerField()),
                ('user', models.ForeignKey(related_name='Documents', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StoredImage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('image', models.CharField(max_length=1024)),
                ('item', models.ForeignKey(related_name='images', blank=True, to='shoutit.Item', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Stream2',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('object_id', models.UUIDField(null=True, blank=True)),
                ('type', models.SmallIntegerField(db_index=True, choices=[(0, 'Profile'), (1, 'Tag'), (2, 'Business'), (3, 'Related'), (4, 'Recommended')])),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('listeners', models.ManyToManyField(related_name='listening', through='shoutit.Listen', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('type', models.IntegerField(default=0)),
                ('State', models.IntegerField(default=0)),
                ('SignUpDate', models.DateTimeField(null=True, blank=True)),
                ('DeactivateDate', models.DateTimeField(null=True, blank=True)),
                ('UserName', models.CharField(max_length=64)),
                ('Password', models.CharField(max_length=24)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('name', models.CharField(db_index=True, unique=True, max_length=30, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(re.compile('[0-9a-z-]{2,30}'), 'Enter a valid tag.', 'invalid')])),
                ('image', models.CharField(max_length=1024, null=True, blank=True)),
                ('DateCreated', models.DateTimeField(auto_now_add=True)),
                ('Definition', models.TextField(default='New Tag!', max_length=512, null=True, blank=True)),
                ('Creator', models.ForeignKey(related_name='TagsCreated', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('Parent', models.ForeignKey(related_name='ChildTags', blank=True, to='shoutit.Tag', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, shoutit.models.base.APIModelMixin),
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('RemoteIdentifier', models.CharField(max_length=1024)),
                ('RemoteData', models.CharField(max_length=1024)),
                ('RemoteStatus', models.CharField(max_length=1024)),
                ('DateCreated', models.DateTimeField(auto_now_add=True)),
                ('DateUpdated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserPermission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('date_given', models.DateTimeField(auto_now_add=True)),
                ('permission', models.ForeignKey(to='shoutit.Permission')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('url', models.URLField(max_length=1024)),
                ('thumbnail_url', models.URLField(max_length=1024)),
                ('provider', models.CharField(max_length=1024)),
                ('id_on_provider', models.CharField(max_length=256)),
                ('duration', models.IntegerField()),
                ('item', models.ForeignKey(related_name='videos', blank=True, to='shoutit.Item', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Voucher',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('code', models.CharField(max_length=22)),
                ('DateGenerated', models.DateTimeField(auto_now_add=True)),
                ('IsValidated', models.BooleanField(default=False)),
                ('IsSent', models.BooleanField(default=False)),
                ('DealBuy', models.ForeignKey(related_name='Vouchers', to='shoutit.DealBuy')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('post_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoutit.Post')),
                ('object_id', models.UUIDField(null=True, blank=True)),
                ('EventType', models.IntegerField(default=0, choices=[(0, 'Follow User'), (1, 'Follow Tag'), (2, 'Shout Offer'), (3, 'Shout Request'), (4, 'Experience'), (5, 'Share Experience'), (6, 'Comment'), (7, 'Post Deal'), (8, 'Buy Deal'), (9, 'Follow Business')])),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('shoutit.post', models.Model),
        ),
        migrations.CreateModel(
            name='Experience',
            fields=[
                ('post_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoutit.Post')),
                ('State', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=('shoutit.post',),
        ),
        migrations.CreateModel(
            name='Shout',
            fields=[
                ('post_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoutit.Post')),
                ('renewal_count', models.PositiveSmallIntegerField(default=0)),
                ('expiry_date', models.DateTimeField(default=None, null=True, db_index=True, blank=True)),
                ('expiry_notified', models.BooleanField(default=False)),
                ('is_sss', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('shoutit.post',),
        ),
        migrations.AddField(
            model_name='stream2',
            name='posts',
            field=models.ManyToManyField(related_name='streams2', to='shoutit.Post'),
        ),
        migrations.AddField(
            model_name='profile',
            name='video',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='shoutit.Video'),
        ),
        migrations.AddField(
            model_name='post',
            name='user',
            field=models.ForeignKey(related_name='Posts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='permission',
            name='users',
            field=models.ManyToManyField(related_name='permissions', through='shoutit.UserPermission', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='payment',
            name='Transaction',
            field=models.ForeignKey(related_name='Payment', to='shoutit.Transaction'),
        ),
        migrations.AddField(
            model_name='payment',
            name='content_type',
            field=models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='user',
            field=models.ForeignKey(related_name='Payments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message2',
            name='deleted_by',
            field=models.ManyToManyField(related_name='deleted_messages2', through='shoutit.Message2Delete', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message2',
            name='read_by',
            field=models.ManyToManyField(related_name='read_messages2', through='shoutit.Message2Read', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message2',
            name='user',
            field=models.ForeignKey(related_name='+', default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='listen',
            name='stream',
            field=models.ForeignKey(to='shoutit.Stream2'),
        ),
        migrations.AddField(
            model_name='featuredtag',
            name='tag',
            field=models.ForeignKey(related_name='featured_in', to='shoutit.Tag'),
        ),
        migrations.AddField(
            model_name='conversation2',
            name='deleted_by',
            field=models.ManyToManyField(related_name='deleted_conversations2', through='shoutit.Conversation2Delete', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='conversation2',
            name='last_message',
            field=models.OneToOneField(related_name='+', null=True, blank=True, to='shoutit.Message2'),
        ),
        migrations.AddField(
            model_name='conversation2',
            name='users',
            field=models.ManyToManyField(related_name='conversations2', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='comment',
            name='AboutPost',
            field=models.ForeignKey(related_name='Comments', blank=True, to='shoutit.Post', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='category',
            name='main_tag',
            field=models.OneToOneField(related_name='+', null=True, blank=True, to='shoutit.Tag'),
        ),
        migrations.AddField(
            model_name='category',
            name='tags',
            field=models.ManyToManyField(related_name='category', to='shoutit.Tag'),
        ),
        migrations.AddField(
            model_name='businesscreateapplication',
            name='LastToken',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='shoutit.ConfirmToken', null=True),
        ),
        migrations.AddField(
            model_name='businesscreateapplication',
            name='business',
            field=models.ForeignKey(related_name='UserApplications', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='shoutit.Business', null=True),
        ),
        migrations.AddField(
            model_name='businesscreateapplication',
            name='user',
            field=models.ForeignKey(related_name='BusinessCreateApplication', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='businessconfirmation',
            name='Files',
            field=models.ManyToManyField(related_name='Confirmation', to='shoutit.StoredFile'),
        ),
        migrations.AddField(
            model_name='businessconfirmation',
            name='user',
            field=models.ForeignKey(related_name='BusinessConfirmations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='business',
            name='Category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='shoutit.BusinessCategory', null=True),
        ),
        migrations.AddField(
            model_name='business',
            name='LastToken',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, blank=True, to='shoutit.ConfirmToken', null=True),
        ),
        migrations.AddField(
            model_name='business',
            name='user',
            field=models.OneToOneField(related_name='business', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions'),
        ),
        migrations.CreateModel(
            name='Deal',
            fields=[
                ('shout_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoutit.Shout')),
                ('MinBuyers', models.IntegerField(default=0)),
                ('MaxBuyers', models.IntegerField(null=True, blank=True)),
                ('OriginalPrice', models.FloatField()),
                ('IsClosed', models.BooleanField(default=False)),
                ('ValidFrom', models.DateTimeField(null=True, blank=True)),
                ('ValidTo', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('shoutit.shout',),
        ),
        migrations.AddField(
            model_name='video',
            name='shout',
            field=models.ForeignKey(related_name='videos', blank=True, to='shoutit.Shout', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='stream2',
            unique_together=set([('content_type', 'object_id', 'type')]),
        ),
        migrations.AddField(
            model_name='storedimage',
            name='shout',
            field=models.ForeignKey(related_name='images', blank=True, to='shoutit.Shout', null=True),
        ),
        migrations.AddField(
            model_name='shout',
            name='category',
            field=models.ForeignKey(related_name='shouts', to='shoutit.Category', null=True),
        ),
        migrations.AddField(
            model_name='shout',
            name='item',
            field=models.OneToOneField(related_name='shout', null=True, blank=True, to='shoutit.Item'),
        ),
        migrations.AddField(
            model_name='shout',
            name='tags',
            field=models.ManyToManyField(related_name='shouts', to='shoutit.Tag'),
        ),
        migrations.AddField(
            model_name='sharedexperience',
            name='Experience',
            field=models.ForeignKey(related_name='SharedExperiences', to='shoutit.Experience'),
        ),
        migrations.AlterUniqueTogether(
            name='message2read',
            unique_together=set([('user', 'message', 'conversation')]),
        ),
        migrations.AlterUniqueTogether(
            name='message2delete',
            unique_together=set([('user', 'message', 'conversation')]),
        ),
        migrations.AlterUniqueTogether(
            name='listen',
            unique_together=set([('listener', 'stream')]),
        ),
        migrations.AlterUniqueTogether(
            name='featuredtag',
            unique_together=set([('country', 'city', 'rank')]),
        ),
        migrations.AddField(
            model_name='experience',
            name='AboutBusiness',
            field=models.ForeignKey(related_name='Experiences', to='shoutit.Business'),
        ),
        migrations.AddField(
            model_name='dbclconversation',
            name='shout',
            field=models.ForeignKey(to='shoutit.Shout'),
        ),
        migrations.AlterUniqueTogether(
            name='conversation2delete',
            unique_together=set([('user', 'conversation')]),
        ),
        migrations.AddField(
            model_name='conversation',
            name='AboutPost',
            field=models.ForeignKey(related_name='+', to='shoutit.Shout'),
        ),
        migrations.AlterUniqueTogether(
            name='sharedexperience',
            unique_together=set([('Experience', 'user')]),
        ),
        migrations.AddField(
            model_name='dealbuy',
            name='Deal',
            field=models.ForeignKey(related_name='Buys', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='shoutit.Deal', null=True),
        ),
    ]
