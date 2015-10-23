# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import re
import shoutit.models.misc
import django.utils.timezone
import django.contrib.auth.models
import django.db.models.deletion
import shoutit.models.base
from django.conf import settings
import django.core.validators
import common.utils
import django.contrib.postgres.fields
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
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='last name', validators=[django.core.validators.MinLengthValidator(1)])),
                ('email', models.EmailField(max_length=254, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('is_activated', models.BooleanField(default=False, help_text='Designates whether this user have a verified email.', verbose_name='activated')),
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
                ('objects', django.contrib.auth.models.UserManager()),
            ],
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
            name='ConfirmToken',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('type', models.IntegerField(default=0)),
                ('token', models.CharField(default=shoutit.models.misc.generate_email_confirm_token, unique=True, max_length=64, db_index=True)),
                ('email', models.EmailField(max_length=254, null=True, blank=True)),
                ('is_disabled', models.BooleanField(default=False)),
                ('user', models.ForeignKey(related_name='confirmation_tokens', to=settings.AUTH_USER_MODEL)),
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
            name='ConversationDelete',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('conversation', models.ForeignKey(related_name='deleted_set', to='shoutit.Conversation')),
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
                ('description', models.CharField(max_length=1000)),
                ('price', models.FloatField(default=0.0)),
                ('state', models.IntegerField(default=0, db_index=True)),
                ('images', django.contrib.postgres.fields.ArrayField(size=None, null=True, base_field=models.URLField(), blank=True)),
                ('currency', models.ForeignKey(related_name='Items', to='shoutit.Currency')),
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
                ('facebook_id', models.CharField(unique=True, max_length=24, db_index=True)),
                ('access_token', models.CharField(max_length=512)),
                ('expires', models.BigIntegerField(default=0)),
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
                ('gplus_id', models.CharField(unique=True, max_length=64, db_index=True)),
                ('credentials_json', models.CharField(max_length=4096)),
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
            name='StreamPost',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'db_table': 'shoutit_stream_posts',
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('text', models.CharField(help_text='The text body of this message, could be None if the message has attachments', max_length=2000, null=True, blank=True)),
                ('conversation', models.ForeignKey(related_name='messages2', to='shoutit.Conversation')),
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
                ('conversation', models.ForeignKey(related_name='messages_attachments', to='shoutit.Conversation')),
                ('message', models.ForeignKey(related_name='attachments', to='shoutit.Message')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MessageDelete',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('conversation', models.ForeignKey(related_name='messages2_deleted_set', to='shoutit.Conversation')),
                ('message', models.ForeignKey(related_name='deleted_set', to='shoutit.Message')),
                ('user', models.ForeignKey(related_name='deleted_messages2_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MessageRead',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('conversation', models.ForeignKey(related_name='messages2_read_set', to='shoutit.Conversation')),
                ('message', models.ForeignKey(related_name='read_set', to='shoutit.Message')),
                ('user', models.ForeignKey(related_name='read_messages2_set', to=settings.AUTH_USER_MODEL)),
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
                ('approved', models.BooleanField(default=False)),
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
                ('image', models.URLField(default='https://user-image.static.shoutit.com/9ca75a6a-fc7e-48f7-9b25-ec71783c28f5-1428689093983.jpg', max_length=1024, blank=True)),
                ('country', models.CharField(default='AE', max_length=200, db_index=True)),
                ('city', models.CharField(default='Dubai', max_length=200, db_index=True)),
                ('latitude', models.FloatField(default=25.1993957)),
                ('longitude', models.FloatField(default=55.2738326)),
                ('gender', models.CharField(max_length=10, null=True, blank=True)),
                ('birthday', models.DateField(null=True, blank=True)),
                ('bio', models.TextField(default='New Shouter!', max_length=512, blank=True)),
                ('user', models.OneToOneField(related_name='profile', to=settings.AUTH_USER_MODEL)),
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
            name='Stream',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, serialize=False, editable=False, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Creation time', null=True)),
                ('modified_at', models.DateTimeField(auto_now=True, verbose_name='Modification time', null=True)),
                ('object_id', models.UUIDField(null=True, blank=True)),
                ('type', models.SmallIntegerField(db_index=True, choices=[(0, 'Profile'), (1, 'Tag'), (2, 'Business'), (3, 'Related'), (4, 'Recommended')])),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('posts', models.ManyToManyField(related_name='streams', through='shoutit.StreamPost', to='shoutit.Post')),
                ('listeners', models.ManyToManyField(related_name='listening', through='shoutit.Listen', to=settings.AUTH_USER_MODEL)),
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
                ('event_type', models.IntegerField(default=0, choices=[(0, 'Listen to User'), (1, 'Listen to Tag'), (2, 'Shout Offer'), (3, 'Shout Request'), (4, 'Shout Experience'), (5, 'Share Experience'), (6, 'Comment'), (7, 'Post Deal'), (8, 'Buy Deal'), (9, 'Listen to Page')])),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('shoutit.post', models.Model),
        ),
        migrations.CreateModel(
            name='Shout',
            fields=[
                ('post_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoutit.Post')),
                ('tags', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(db_index=True, unique=True, max_length=30, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(re.compile('[0-9a-z-]{2,30}'), 'Enter a valid tag.', 'invalid')]), size=None)),
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
            model_name='profile',
            name='video',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='shoutit.Video'),
        ),
        migrations.AddField(
            model_name='post',
            name='user',
            field=models.ForeignKey(related_name='Posts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='deleted_by',
            field=models.ManyToManyField(related_name='deleted_messages2', through='shoutit.MessageDelete', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='read_by',
            field=models.ManyToManyField(related_name='read_messages2', through='shoutit.MessageRead', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='message',
            name='user',
            field=models.ForeignKey(related_name='+', default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='listen',
            name='stream',
            field=models.ForeignKey(to='shoutit.Stream'),
        ),
        migrations.AddField(
            model_name='streampost',
            name='stream',
            field=models.ForeignKey(to='shoutit.Stream'),
        ),
        migrations.AddField(
            model_name='streampost',
            name='post',
            field=models.ForeignKey(to='shoutit.Post'),
        ),
        migrations.AddField(
            model_name='item',
            name='videos',
            field=models.ManyToManyField(to='shoutit.Video', blank=True),
        ),
        migrations.AddField(
            model_name='featuredtag',
            name='tag',
            field=models.ForeignKey(related_name='featured_in', to='shoutit.Tag'),
        ),
        migrations.AddField(
            model_name='conversation',
            name='deleted_by',
            field=models.ManyToManyField(related_name='deleted_conversations2', through='shoutit.ConversationDelete', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='conversation',
            name='last_message',
            field=models.OneToOneField(related_name='+', null=True, blank=True, to='shoutit.Message'),
        ),
        migrations.AddField(
            model_name='conversation',
            name='users',
            field=models.ManyToManyField(related_name='conversations2', to=settings.AUTH_USER_MODEL),
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
            model_name='user',
            name='permissions',
            field=models.ManyToManyField(to='shoutit.Permission', through='shoutit.UserPermission'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions'),
        ),
        migrations.AlterUniqueTogether(
            name='stream',
            unique_together=set([('content_type', 'object_id', 'type')]),
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
        migrations.AlterUniqueTogether(
            name='messageread',
            unique_together=set([('user', 'message', 'conversation')]),
        ),
        migrations.AlterUniqueTogether(
            name='messagedelete',
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
            model_name='dbclconversation',
            name='shout',
            field=models.ForeignKey(to='shoutit.Shout'),
        ),
        migrations.AlterUniqueTogether(
            name='conversationdelete',
            unique_together=set([('user', 'conversation')]),
        ),
    ]
