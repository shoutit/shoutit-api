# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PredefinedCity'
        db.create_table(u'shoutit_predefinedcity', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('City', self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=200, db_index=True)),
            ('EncodedCity', self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=200, db_index=True)),
            ('Country', self.gf('django.db.models.fields.CharField')(default='', max_length=2, db_index=True)),
            ('Latitude', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('Longitude', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('Approved', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('shoutit', ['PredefinedCity'])

        # Adding model 'StoredFile'
        db.create_table(u'shoutit_storedfile', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Documents', null=True, to=orm['auth.User'])),
            ('File', self.gf('django.db.models.fields.URLField')(max_length=1024)),
            ('Type', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('shoutit', ['StoredFile'])

        # Adding model 'ConfirmToken'
        db.create_table(u'shoutit_confirmtoken', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Token', self.gf('django.db.models.fields.CharField')(unique=True, max_length=24, db_index=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Tokens', to=orm['auth.User'])),
            ('Type', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('DateCreated', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('Email', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('IsDisabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('shoutit', ['ConfirmToken'])

        # Adding model 'FbContest'
        db.create_table(u'shoutit_fbcontest', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('ContestId', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Contest_1', to=orm['auth.User'])),
            ('FbId', self.gf('django.db.models.fields.CharField')(max_length=24, db_index=True)),
            ('ShareId', self.gf('django.db.models.fields.CharField')(default=None, max_length=50, null=True)),
        ))
        db.send_create_signal('shoutit', ['FbContest'])

        # Adding model 'Item'
        db.create_table(u'shoutit_item', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Name', self.gf('django.db.models.fields.CharField')(default='', max_length=512)),
            ('Description', self.gf('django.db.models.fields.CharField')(default='', max_length=1000)),
            ('Price', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('Currency', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Items', to=orm['shoutit.Currency'])),
            ('State', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('DateCreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('shoutit', ['Item'])

        # Adding model 'Currency'
        db.create_table(u'shoutit_currency', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('Country', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('Name', self.gf('django.db.models.fields.CharField')(max_length=64, null=True)),
        ))
        db.send_create_signal('shoutit', ['Currency'])

        # Adding model 'Stream'
        db.create_table(u'shoutit_stream', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Type', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
        ))
        db.send_create_signal('shoutit', ['Stream'])

        # Adding model 'Stream2'
        db.create_table(u'shoutit_stream2', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('type', self.gf('django.db.models.fields.SmallIntegerField')(db_index=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, blank=True)),
        ))
        db.send_create_signal('shoutit', ['Stream2'])

        # Adding unique constraint on 'Stream2', fields ['content_type', 'object_uuid', 'type']
        db.create_unique(u'shoutit_stream2', ['content_type_id', 'object_uuid', 'type'])

        # Adding M2M table for field posts on 'Stream2'
        m2m_table_name = db.shorten_name(u'shoutit_stream2_posts')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('stream2', models.ForeignKey(orm['shoutit.stream2'], null=False)),
            ('post', models.ForeignKey(orm['shoutit.post'], null=False))
        ))
        db.create_unique(m2m_table_name, ['stream2_id', 'post_id'])

        # Adding model 'Listen'
        db.create_table(u'shoutit_listen', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('listener', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('stream', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shoutit.Stream2'])),
            ('date_listened', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('shoutit', ['Listen'])

        # Adding unique constraint on 'Listen', fields ['listener', 'stream']
        db.create_unique(u'shoutit_listen', ['listener_id', 'stream_id'])

        # Adding model 'Tag'
        db.create_table(u'shoutit_tag', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Name', self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=100, db_index=True)),
            ('Creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='TagsCreated', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('Image', self.gf('django.db.models.fields.URLField')(default='/static/img/shout_tag.png', max_length=1024, null=True)),
            ('DateCreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('Parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='ChildTags', null=True, to=orm['shoutit.Tag'])),
            ('Stream', self.gf('django.db.models.fields.related.OneToOneField')(related_name='OwnerTag', unique=True, null=True, to=orm['shoutit.Stream'])),
            ('Definition', self.gf('django.db.models.fields.TextField')(default='New Tag!', max_length=512, null=True)),
        ))
        db.send_create_signal('shoutit', ['Tag'])

        # Adding model 'Category'
        db.create_table(u'shoutit_category', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Name', self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=100, db_index=True)),
            ('DateCreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('TopTag', self.gf('django.db.models.fields.related.OneToOneField')(related_name='OwnerCategory', unique=True, null=True, to=orm['shoutit.Tag'])),
        ))
        db.send_create_signal('shoutit', ['Category'])

        # Adding M2M table for field Tags on 'Category'
        m2m_table_name = db.shorten_name(u'shoutit_category_Tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('category', models.ForeignKey(orm['shoutit.category'], null=False)),
            ('tag', models.ForeignKey(orm['shoutit.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['category_id', 'tag_id'])

        # Adding model 'BusinessCategory'
        db.create_table(u'shoutit_businesscategory', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Name', self.gf('django.db.models.fields.CharField')(max_length=1024, db_index=True)),
            ('Source', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('SourceID', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('Parent', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='children', null=True, to=orm['shoutit.BusinessCategory'])),
        ))
        db.send_create_signal('shoutit', ['BusinessCategory'])

        # Adding model 'Business'
        db.create_table(u'shoutit_business', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='business', unique=True, to=orm['auth.User'])),
            ('Name', self.gf('django.db.models.fields.CharField')(max_length=1024, db_index=True)),
            ('Category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shoutit.BusinessCategory'], null=True, on_delete=models.SET_NULL)),
            ('Image', self.gf('django.db.models.fields.URLField')(max_length=1024, null=True)),
            ('About', self.gf('django.db.models.fields.TextField')(default='', max_length=512, null=True)),
            ('Phone', self.gf('django.db.models.fields.CharField')(max_length=20, unique=True, null=True)),
            ('Website', self.gf('django.db.models.fields.URLField')(max_length=1024, null=True)),
            ('Country', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, db_index=True)),
            ('City', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, db_index=True)),
            ('Latitude', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('Longitude', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('Address', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, db_index=True)),
            ('Stream', self.gf('django.db.models.fields.related.OneToOneField')(related_name='OwnerBusiness', unique=True, null=True, to=orm['shoutit.Stream'])),
            ('LastToken', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['shoutit.ConfirmToken'], null=True, on_delete=models.SET_NULL)),
            ('Confirmed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('shoutit', ['Business'])

        # Adding model 'BusinessCreateApplication'
        db.create_table(u'shoutit_businesscreateapplication', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='BusinessCreateApplication', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('business', self.gf('django.db.models.fields.related.ForeignKey')(related_name='UserApplications', null=True, on_delete=models.SET_NULL, to=orm['shoutit.Business'])),
            ('Name', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, db_index=True)),
            ('Category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shoutit.BusinessCategory'], null=True, on_delete=models.SET_NULL)),
            ('Image', self.gf('django.db.models.fields.URLField')(max_length=1024, null=True)),
            ('About', self.gf('django.db.models.fields.TextField')(default='', max_length=512, null=True)),
            ('Phone', self.gf('django.db.models.fields.CharField')(max_length=20, null=True)),
            ('Website', self.gf('django.db.models.fields.URLField')(max_length=1024, null=True)),
            ('Longitude', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('Latitude', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('Country', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, db_index=True)),
            ('City', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, db_index=True)),
            ('Address', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, db_index=True)),
            ('LastToken', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['shoutit.ConfirmToken'], null=True, on_delete=models.SET_NULL)),
            ('DateApplied', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('Status', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
        ))
        db.send_create_signal('shoutit', ['BusinessCreateApplication'])

        # Adding model 'BusinessSource'
        db.create_table(u'shoutit_businesssource', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('business', self.gf('django.db.models.fields.related.OneToOneField')(related_name='Source', unique=True, to=orm['shoutit.Business'])),
            ('Source', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('SourceID', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
        ))
        db.send_create_signal('shoutit', ['BusinessSource'])

        # Adding model 'BusinessConfirmation'
        db.create_table(u'shoutit_businessconfirmation', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='BusinessConfirmations', to=orm['auth.User'])),
            ('DateSent', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('shoutit', ['BusinessConfirmation'])

        # Adding M2M table for field Files on 'BusinessConfirmation'
        m2m_table_name = db.shorten_name(u'shoutit_businessconfirmation_Files')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('businessconfirmation', models.ForeignKey(orm['shoutit.businessconfirmation'], null=False)),
            ('storedfile', models.ForeignKey(orm['shoutit.storedfile'], null=False))
        ))
        db.create_unique(m2m_table_name, ['businessconfirmation_id', 'storedfile_id'])

        # Adding model 'GalleryItem'
        db.create_table(u'shoutit_galleryitem', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['shoutit.Item'])),
            ('Gallery', self.gf('django.db.models.fields.related.ForeignKey')(related_name='GalleryItems', to=orm['shoutit.Gallery'])),
            ('IsDisable', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('IsMuted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('DateCreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('shoutit', ['GalleryItem'])

        # Adding unique constraint on 'GalleryItem', fields ['Item', 'Gallery']
        db.create_unique(u'shoutit_galleryitem', ['Item_id', 'Gallery_id'])

        # Adding model 'Gallery'
        db.create_table(u'shoutit_gallery', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Description', self.gf('django.db.models.fields.TextField')(default='', max_length=500)),
            ('OwnerBusiness', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Galleries', to=orm['shoutit.Business'])),
            ('Category', self.gf('django.db.models.fields.related.OneToOneField')(related_name='+', unique=True, null=True, to=orm['shoutit.Category'])),
        ))
        db.send_create_signal('shoutit', ['Gallery'])

        # Adding model 'Profile'
        db.create_table(u'shoutit_profile', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='profile', unique=True, null=True, to=orm['auth.User'])),
            ('Image', self.gf('django.db.models.fields.URLField')(max_length=1024, null=True)),
            ('Country', self.gf('django.db.models.fields.CharField')(default='AE', max_length=200, db_index=True)),
            ('City', self.gf('django.db.models.fields.CharField')(default='Dubai', max_length=200, db_index=True)),
            ('Latitude', self.gf('django.db.models.fields.FloatField')(default=25.1993957)),
            ('Longitude', self.gf('django.db.models.fields.FloatField')(default=55.2738326)),
            ('Bio', self.gf('django.db.models.fields.TextField')(default='New Shouter!', max_length=512, null=True)),
            ('Mobile', self.gf('django.db.models.fields.CharField')(max_length=20, unique=True, null=True)),
            ('Stream', self.gf('django.db.models.fields.related.OneToOneField')(related_name='OwnerUser', unique=True, to=orm['shoutit.Stream'])),
            ('birthday', self.gf('django.db.models.fields.DateField')(null=True)),
            ('Sex', self.gf('django.db.models.fields.NullBooleanField')(default=True, null=True, blank=True)),
            ('LastToken', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['shoutit.ConfirmToken'], null=True, on_delete=models.SET_NULL)),
            ('isSSS', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('isSMS', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
        ))
        db.send_create_signal('shoutit', ['Profile'])

        # Adding M2M table for field Interests on 'Profile'
        m2m_table_name = db.shorten_name(u'shoutit_profile_Interests')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('profile', models.ForeignKey(orm['shoutit.profile'], null=False)),
            ('tag', models.ForeignKey(orm['shoutit.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['profile_id', 'tag_id'])

        # Adding model 'LinkedFacebookAccount'
        db.create_table(u'shoutit_linkedfacebookaccount', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='linked_facebook', unique=True, to=orm['auth.User'])),
            ('facebook_id', self.gf('django.db.models.fields.CharField')(max_length=24, db_index=True)),
            ('AccessToken', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('ExpiresIn', self.gf('django.db.models.fields.BigIntegerField')(default=0)),
        ))
        db.send_create_signal('shoutit', ['LinkedFacebookAccount'])

        # Adding model 'LinkedGoogleAccount'
        db.create_table(u'shoutit_linkedgoogleaccount', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='linked_gplus', unique=True, to=orm['auth.User'])),
            ('credentials_json', self.gf('django.db.models.fields.CharField')(max_length=2048)),
            ('gplus_id', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
        ))
        db.send_create_signal('shoutit', ['LinkedGoogleAccount'])

        # Adding model 'Permission'
        db.create_table(u'shoutit_permission', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512, db_index=True)),
        ))
        db.send_create_signal('shoutit', ['Permission'])

        # Adding model 'UserPermission'
        db.create_table(u'shoutit_userpermission', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('permission', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shoutit.Permission'])),
            ('date_given', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('shoutit', ['UserPermission'])

        # Adding model 'FollowShip'
        db.create_table(u'shoutit_followship', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('follower', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shoutit.Profile'])),
            ('stream', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shoutit.Stream'])),
            ('date_followed', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('state', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
        ))
        db.send_create_signal('shoutit', ['FollowShip'])

        # Adding model 'Post'
        db.create_table(u'shoutit_post', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('OwnerUser', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Posts', to=orm['auth.User'])),
            ('Text', self.gf('django.db.models.fields.TextField')(default='', max_length=2000, db_index=True)),
            ('Type', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True)),
            ('DatePublished', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('IsMuted', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('IsDisabled', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('Longitude', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('Latitude', self.gf('django.db.models.fields.FloatField')(default=0.0)),
            ('CountryCode', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, db_index=True)),
            ('ProvinceCode', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, db_index=True)),
            ('Address', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, db_index=True)),
        ))
        db.send_create_signal('shoutit', ['Post'])

        # Adding M2M table for field Streams on 'Post'
        m2m_table_name = db.shorten_name(u'shoutit_post_Streams')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('post', models.ForeignKey(orm['shoutit.post'], null=False)),
            ('stream', models.ForeignKey(orm['shoutit.stream'], null=False))
        ))
        db.create_unique(m2m_table_name, ['post_id', 'stream_id'])

        # Adding model 'Shout'
        db.create_table(u'shoutit_shout', (
            (u'post_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['shoutit.Post'], unique=True, primary_key=True)),
            ('ExpiryDate', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, db_index=True)),
            ('ExpiryNotified', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('shoutit', ['Shout'])

        # Adding M2M table for field Tags on 'Shout'
        m2m_table_name = db.shorten_name(u'shoutit_shout_Tags')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('shout', models.ForeignKey(orm['shoutit.shout'], null=False)),
            ('tag', models.ForeignKey(orm['shoutit.tag'], null=False))
        ))
        db.create_unique(m2m_table_name, ['shout_id', 'tag_id'])

        # Adding model 'ShoutWrap'
        db.create_table(u'shoutit_shoutwrap', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Shout', self.gf('django.db.models.fields.related.ForeignKey')(related_name='ShoutWraps', to=orm['shoutit.Shout'])),
            ('Stream', self.gf('django.db.models.fields.related.ForeignKey')(related_name='ShoutWraps', to=orm['shoutit.Stream'])),
            ('Rank', self.gf('django.db.models.fields.FloatField')(default=1.0)),
        ))
        db.send_create_signal('shoutit', ['ShoutWrap'])

        # Adding model 'Trade'
        db.create_table(u'shoutit_trade', (
            (u'shout_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['shoutit.Shout'], unique=True, primary_key=True)),
            ('Item', self.gf('django.db.models.fields.related.OneToOneField')(related_name='Shout', unique=True, null=True, to=orm['shoutit.Item'])),
            ('RelatedStream', self.gf('django.db.models.fields.related.OneToOneField')(related_name='InitShoutRelated', unique=True, null=True, to=orm['shoutit.Stream'])),
            ('RecommendedStream', self.gf('django.db.models.fields.related.OneToOneField')(related_name='InitShoutRecommended', unique=True, null=True, to=orm['shoutit.Stream'])),
            ('StreamsCode', self.gf('django.db.models.fields.CharField')(default='', max_length=2000)),
            ('MaxFollowings', self.gf('django.db.models.fields.IntegerField')(default=6)),
            ('MaxDistance', self.gf('django.db.models.fields.FloatField')(default=180.0)),
            ('MaxPrice', self.gf('django.db.models.fields.FloatField')(default=1.0)),
            ('IsShowMobile', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('IsSSS', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('BaseDatePublished', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('RenewalCount', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('shoutit', ['Trade'])

        # Adding model 'Deal'
        db.create_table(u'shoutit_deal', (
            (u'shout_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['shoutit.Shout'], unique=True, primary_key=True)),
            ('MinBuyers', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('MaxBuyers', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('OriginalPrice', self.gf('django.db.models.fields.FloatField')()),
            ('IsClosed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('Item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Deals', null=True, on_delete=models.SET_NULL, to=orm['shoutit.Item'])),
            ('ValidFrom', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('ValidTo', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('shoutit', ['Deal'])

        # Adding model 'Experience'
        db.create_table(u'shoutit_experience', (
            (u'post_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['shoutit.Post'], unique=True, primary_key=True)),
            ('AboutBusiness', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Experiences', to=orm['shoutit.Business'])),
            ('State', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('shoutit', ['Experience'])

        # Adding model 'SharedExperience'
        db.create_table(u'shoutit_sharedexperience', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Experience', self.gf('django.db.models.fields.related.ForeignKey')(related_name='SharedExperiences', to=orm['shoutit.Experience'])),
            ('OwnerUser', self.gf('django.db.models.fields.related.ForeignKey')(related_name='SharedExperiences', to=orm['auth.User'])),
            ('DateCreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('shoutit', ['SharedExperience'])

        # Adding unique constraint on 'SharedExperience', fields ['Experience', 'OwnerUser']
        db.create_unique(u'shoutit_sharedexperience', ['Experience_id', 'OwnerUser_id'])

        # Adding model 'Video'
        db.create_table(u'shoutit_video', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('shout', self.gf('django.db.models.fields.related.ForeignKey')(related_name='videos', null=True, to=orm['shoutit.Shout'])),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='videos', null=True, to=orm['shoutit.Item'])),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=1024)),
            ('thumbnail_url', self.gf('django.db.models.fields.URLField')(max_length=1024)),
            ('provider', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('id_on_provider', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('duration', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('shoutit', ['Video'])

        # Adding model 'StoredImage'
        db.create_table(u'shoutit_storedimage', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Shout', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Images', null=True, to=orm['shoutit.Shout'])),
            ('Item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Images', null=True, to=orm['shoutit.Item'])),
            ('Image', self.gf('django.db.models.fields.URLField')(max_length=1024)),
        ))
        db.send_create_signal('shoutit', ['StoredImage'])

        # Adding model 'Comment'
        db.create_table(u'shoutit_comment', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('AboutPost', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Comments', null=True, to=orm['shoutit.Post'])),
            ('OwnerUser', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['auth.User'])),
            ('IsDisabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('Text', self.gf('django.db.models.fields.TextField')(max_length=300)),
            ('DateCreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('shoutit', ['Comment'])

        # Adding model 'Event'
        db.create_table(u'shoutit_event', (
            (u'post_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['shoutit.Post'], unique=True, primary_key=True)),
            ('EventType', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True)),
            ('object_pk', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('shoutit', ['Event'])

        # Adding model 'Conversation'
        db.create_table(u'shoutit_conversation', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('FromUser', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['auth.User'])),
            ('ToUser', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['auth.User'])),
            ('AboutPost', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['shoutit.Trade'])),
            ('IsRead', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('VisibleToRecivier', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('VisibleToSender', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('shoutit', ['Conversation'])

        # Adding model 'Message'
        db.create_table(u'shoutit_message', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Conversation', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Messages', to=orm['shoutit.Conversation'])),
            ('FromUser', self.gf('django.db.models.fields.related.ForeignKey')(related_name='received_messages', to=orm['auth.User'])),
            ('ToUser', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sent_messages', to=orm['auth.User'])),
            ('Text', self.gf('django.db.models.fields.TextField')(null=True)),
            ('IsRead', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('VisibleToRecivier', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('VisibleToSender', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('DateCreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('shoutit', ['Message'])

        # Adding model 'MessageAttachment'
        db.create_table(u'shoutit_messageattachment', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('message', self.gf('django.db.models.fields.related.ForeignKey')(related_name='attachments', to=orm['shoutit.Message'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('shoutit', ['MessageAttachment'])

        # Adding model 'Notification'
        db.create_table(u'shoutit_notification', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('ToUser', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Notifications', to=orm['auth.User'])),
            ('FromUser', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='+', null=True, to=orm['auth.User'])),
            ('IsRead', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('Type', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('DateCreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True)),
            ('object_pk', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('shoutit', ['Notification'])

        # Adding model 'Report'
        db.create_table(u'shoutit_report', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Reports', to=orm['auth.User'])),
            ('Text', self.gf('django.db.models.fields.TextField')(default='', max_length=300)),
            ('IsSolved', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('IsDisabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('DateCreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True)),
            ('object_pk', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('shoutit', ['Report'])

        # Adding model 'Payment'
        db.create_table(u'shoutit_payment', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Payments', to=orm['auth.User'])),
            ('DateCreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('DateUpdated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('Amount', self.gf('django.db.models.fields.FloatField')()),
            ('Currency', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['shoutit.Currency'])),
            ('Status', self.gf('django.db.models.fields.IntegerField')()),
            ('Transaction', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Payment', to=orm['shoutit.Transaction'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True)),
            ('object_pk', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('shoutit', ['Payment'])

        # Adding model 'Transaction'
        db.create_table(u'shoutit_transaction', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('RemoteIdentifier', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('RemoteData', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('RemoteStatus', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('DateCreated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('DateUpdated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('shoutit', ['Transaction'])

        # Adding model 'Voucher'
        db.create_table(u'shoutit_voucher', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('DealBuy', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Vouchers', to=orm['shoutit.DealBuy'])),
            ('Code', self.gf('django.db.models.fields.CharField')(max_length=22)),
            ('DateGenerated', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('IsValidated', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('IsSent', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('shoutit', ['Voucher'])

        # Adding model 'DealBuy'
        db.create_table(u'shoutit_dealbuy', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Deal', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Buys', null=True, on_delete=models.SET_NULL, to=orm['shoutit.Deal'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='DealsBought', null=True, on_delete=models.SET_NULL, to=orm['auth.User'])),
            ('Amount', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('DateBought', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('shoutit', ['DealBuy'])

        # Adding model 'Service'
        db.create_table(u'shoutit_service', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Code', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('Name', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('Price', self.gf('django.db.models.fields.FloatField')()),
        ))
        db.send_create_signal('shoutit', ['Service'])

        # Adding model 'ServiceBuy'
        db.create_table(u'shoutit_servicebuy', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Services', to=orm['auth.User'])),
            ('Service', self.gf('django.db.models.fields.related.ForeignKey')(related_name='Buyers', to=orm['shoutit.Service'])),
            ('Amount', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('DateBought', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('shoutit', ['ServiceBuy'])

        # Adding model 'ServiceUsage'
        db.create_table(u'shoutit_serviceusage', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='ServicesUsages', to=orm['auth.User'])),
            ('Service', self.gf('django.db.models.fields.related.ForeignKey')(related_name='BuyersUsages', to=orm['shoutit.Service'])),
            ('Amount', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('DateUsed', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('shoutit', ['ServiceUsage'])

        # Adding model 'Subscription'
        db.create_table(u'shoutit_subscription', (
            ('uuid', self.gf('uuidfield.fields.UUIDField')(unique=True, max_length=36, primary_key=True)),
            ('Type', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('State', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('SignUpDate', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('DeactivateDate', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('UserName', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('Password', self.gf('django.db.models.fields.CharField')(max_length=24)),
        ))
        db.send_create_signal('shoutit', ['Subscription'])


    def backwards(self, orm):
        # Removing unique constraint on 'SharedExperience', fields ['Experience', 'OwnerUser']
        db.delete_unique(u'shoutit_sharedexperience', ['Experience_id', 'OwnerUser_id'])

        # Removing unique constraint on 'GalleryItem', fields ['Item', 'Gallery']
        db.delete_unique(u'shoutit_galleryitem', ['Item_id', 'Gallery_id'])

        # Removing unique constraint on 'Listen', fields ['listener', 'stream']
        db.delete_unique(u'shoutit_listen', ['listener_id', 'stream_id'])

        # Removing unique constraint on 'Stream2', fields ['content_type', 'object_uuid', 'type']
        db.delete_unique(u'shoutit_stream2', ['content_type_id', 'object_uuid', 'type'])

        # Deleting model 'PredefinedCity'
        db.delete_table(u'shoutit_predefinedcity')

        # Deleting model 'StoredFile'
        db.delete_table(u'shoutit_storedfile')

        # Deleting model 'ConfirmToken'
        db.delete_table(u'shoutit_confirmtoken')

        # Deleting model 'FbContest'
        db.delete_table(u'shoutit_fbcontest')

        # Deleting model 'Item'
        db.delete_table(u'shoutit_item')

        # Deleting model 'Currency'
        db.delete_table(u'shoutit_currency')

        # Deleting model 'Stream'
        db.delete_table(u'shoutit_stream')

        # Deleting model 'Stream2'
        db.delete_table(u'shoutit_stream2')

        # Removing M2M table for field posts on 'Stream2'
        db.delete_table(db.shorten_name(u'shoutit_stream2_posts'))

        # Deleting model 'Listen'
        db.delete_table(u'shoutit_listen')

        # Deleting model 'Tag'
        db.delete_table(u'shoutit_tag')

        # Deleting model 'Category'
        db.delete_table(u'shoutit_category')

        # Removing M2M table for field Tags on 'Category'
        db.delete_table(db.shorten_name(u'shoutit_category_Tags'))

        # Deleting model 'BusinessCategory'
        db.delete_table(u'shoutit_businesscategory')

        # Deleting model 'Business'
        db.delete_table(u'shoutit_business')

        # Deleting model 'BusinessCreateApplication'
        db.delete_table(u'shoutit_businesscreateapplication')

        # Deleting model 'BusinessSource'
        db.delete_table(u'shoutit_businesssource')

        # Deleting model 'BusinessConfirmation'
        db.delete_table(u'shoutit_businessconfirmation')

        # Removing M2M table for field Files on 'BusinessConfirmation'
        db.delete_table(db.shorten_name(u'shoutit_businessconfirmation_Files'))

        # Deleting model 'GalleryItem'
        db.delete_table(u'shoutit_galleryitem')

        # Deleting model 'Gallery'
        db.delete_table(u'shoutit_gallery')

        # Deleting model 'Profile'
        db.delete_table(u'shoutit_profile')

        # Removing M2M table for field Interests on 'Profile'
        db.delete_table(db.shorten_name(u'shoutit_profile_Interests'))

        # Deleting model 'LinkedFacebookAccount'
        db.delete_table(u'shoutit_linkedfacebookaccount')

        # Deleting model 'LinkedGoogleAccount'
        db.delete_table(u'shoutit_linkedgoogleaccount')

        # Deleting model 'Permission'
        db.delete_table(u'shoutit_permission')

        # Deleting model 'UserPermission'
        db.delete_table(u'shoutit_userpermission')

        # Deleting model 'FollowShip'
        db.delete_table(u'shoutit_followship')

        # Deleting model 'Post'
        db.delete_table(u'shoutit_post')

        # Removing M2M table for field Streams on 'Post'
        db.delete_table(db.shorten_name(u'shoutit_post_Streams'))

        # Deleting model 'Shout'
        db.delete_table(u'shoutit_shout')

        # Removing M2M table for field Tags on 'Shout'
        db.delete_table(db.shorten_name(u'shoutit_shout_Tags'))

        # Deleting model 'ShoutWrap'
        db.delete_table(u'shoutit_shoutwrap')

        # Deleting model 'Trade'
        db.delete_table(u'shoutit_trade')

        # Deleting model 'Deal'
        db.delete_table(u'shoutit_deal')

        # Deleting model 'Experience'
        db.delete_table(u'shoutit_experience')

        # Deleting model 'SharedExperience'
        db.delete_table(u'shoutit_sharedexperience')

        # Deleting model 'Video'
        db.delete_table(u'shoutit_video')

        # Deleting model 'StoredImage'
        db.delete_table(u'shoutit_storedimage')

        # Deleting model 'Comment'
        db.delete_table(u'shoutit_comment')

        # Deleting model 'Event'
        db.delete_table(u'shoutit_event')

        # Deleting model 'Conversation'
        db.delete_table(u'shoutit_conversation')

        # Deleting model 'Message'
        db.delete_table(u'shoutit_message')

        # Deleting model 'MessageAttachment'
        db.delete_table(u'shoutit_messageattachment')

        # Deleting model 'Notification'
        db.delete_table(u'shoutit_notification')

        # Deleting model 'Report'
        db.delete_table(u'shoutit_report')

        # Deleting model 'Payment'
        db.delete_table(u'shoutit_payment')

        # Deleting model 'Transaction'
        db.delete_table(u'shoutit_transaction')

        # Deleting model 'Voucher'
        db.delete_table(u'shoutit_voucher')

        # Deleting model 'DealBuy'
        db.delete_table(u'shoutit_dealbuy')

        # Deleting model 'Service'
        db.delete_table(u'shoutit_service')

        # Deleting model 'ServiceBuy'
        db.delete_table(u'shoutit_servicebuy')

        # Deleting model 'ServiceUsage'
        db.delete_table(u'shoutit_serviceusage')

        # Deleting model 'Subscription'
        db.delete_table(u'shoutit_subscription')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'shoutit.business': {
            'About': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '512', 'null': 'True'}),
            'Address': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'db_index': 'True'}),
            'Category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.BusinessCategory']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'City': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'db_index': 'True'}),
            'Confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Country': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'db_index': 'True'}),
            'Image': ('django.db.models.fields.URLField', [], {'max_length': '1024', 'null': 'True'}),
            'LastToken': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['shoutit.ConfirmToken']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'Latitude': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'Longitude': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'Meta': {'object_name': 'Business'},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'db_index': 'True'}),
            'Phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'unique': 'True', 'null': 'True'}),
            'Stream': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'OwnerBusiness'", 'unique': 'True', 'null': 'True', 'to': "orm['shoutit.Stream']"}),
            'Website': ('django.db.models.fields.URLField', [], {'max_length': '1024', 'null': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'business'", 'unique': 'True', 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.businesscategory': {
            'Meta': {'object_name': 'BusinessCategory'},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'db_index': 'True'}),
            'Parent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'children'", 'null': 'True', 'to': "orm['shoutit.BusinessCategory']"}),
            'Source': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'SourceID': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.businessconfirmation': {
            'DateSent': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Files': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'Confirmation'", 'symmetrical': 'False', 'to': "orm['shoutit.StoredFile']"}),
            'Meta': {'object_name': 'BusinessConfirmation'},
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'BusinessConfirmations'", 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.businesscreateapplication': {
            'About': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '512', 'null': 'True'}),
            'Address': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'db_index': 'True'}),
            'Category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.BusinessCategory']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'City': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'db_index': 'True'}),
            'Country': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'db_index': 'True'}),
            'DateApplied': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Image': ('django.db.models.fields.URLField', [], {'max_length': '1024', 'null': 'True'}),
            'LastToken': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['shoutit.ConfirmToken']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'Latitude': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'Longitude': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'Meta': {'object_name': 'BusinessCreateApplication'},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'db_index': 'True'}),
            'Phone': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'Status': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'Website': ('django.db.models.fields.URLField', [], {'max_length': '1024', 'null': 'True'}),
            'business': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'UserApplications'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['shoutit.Business']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'BusinessCreateApplication'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.businesssource': {
            'Meta': {'object_name': 'BusinessSource'},
            'Source': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'SourceID': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'business': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'Source'", 'unique': 'True', 'to': "orm['shoutit.Business']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.category': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'Category'},
            'Name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'Tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'Category'", 'symmetrical': 'False', 'to': "orm['shoutit.Tag']"}),
            'TopTag': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'OwnerCategory'", 'unique': 'True', 'null': 'True', 'to': "orm['shoutit.Tag']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.comment': {
            'AboutPost': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Comments'", 'null': 'True', 'to': "orm['shoutit.Post']"}),
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'IsDisabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Comment'},
            'OwnerUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['auth.User']"}),
            'Text': ('django.db.models.fields.TextField', [], {'max_length': '300'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.confirmtoken': {
            'DateCreated': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Email': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'IsDisabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'ConfirmToken'},
            'Token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '24', 'db_index': 'True'}),
            'Type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Tokens'", 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.conversation': {
            'AboutPost': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['shoutit.Trade']"}),
            'FromUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['auth.User']"}),
            'IsRead': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Conversation'},
            'ToUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['auth.User']"}),
            'VisibleToRecivier': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'VisibleToSender': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.currency': {
            'Code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'Country': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'Meta': {'object_name': 'Currency'},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.deal': {
            'IsClosed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Deals'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['shoutit.Item']"}),
            'MaxBuyers': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'Meta': {'object_name': 'Deal', '_ormbases': ['shoutit.Shout']},
            'MinBuyers': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'OriginalPrice': ('django.db.models.fields.FloatField', [], {}),
            'ValidFrom': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'ValidTo': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            u'shout_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['shoutit.Shout']", 'unique': 'True', 'primary_key': 'True'})
        },
        'shoutit.dealbuy': {
            'Amount': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'DateBought': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Deal': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Buys'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['shoutit.Deal']"}),
            'Meta': {'object_name': 'DealBuy'},
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'DealsBought'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.event': {
            'EventType': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Meta': {'object_name': 'Event', '_ormbases': ['shoutit.Post']},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'object_pk': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'post_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['shoutit.Post']", 'unique': 'True', 'primary_key': 'True'})
        },
        'shoutit.experience': {
            'AboutBusiness': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Experiences'", 'to': "orm['shoutit.Business']"}),
            'Meta': {'object_name': 'Experience', '_ormbases': ['shoutit.Post']},
            'State': ('django.db.models.fields.IntegerField', [], {}),
            u'post_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['shoutit.Post']", 'unique': 'True', 'primary_key': 'True'})
        },
        'shoutit.fbcontest': {
            'ContestId': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'FbId': ('django.db.models.fields.CharField', [], {'max_length': '24', 'db_index': 'True'}),
            'Meta': {'object_name': 'FbContest'},
            'ShareId': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '50', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Contest_1'", 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.followship': {
            'Meta': {'object_name': 'FollowShip'},
            'date_followed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'follower': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.Profile']"}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.Stream']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.gallery': {
            'Category': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'to': "orm['shoutit.Category']"}),
            'Description': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '500'}),
            'Meta': {'object_name': 'Gallery'},
            'OwnerBusiness': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Galleries'", 'to': "orm['shoutit.Business']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.galleryitem': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Gallery': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'GalleryItems'", 'to': "orm['shoutit.Gallery']"}),
            'IsDisable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'IsMuted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['shoutit.Item']"}),
            'Meta': {'unique_together': "(('Item', 'Gallery'),)", 'object_name': 'GalleryItem'},
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.item': {
            'Currency': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Items'", 'to': "orm['shoutit.Currency']"}),
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000'}),
            'Meta': {'object_name': 'Item'},
            'Name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512'}),
            'Price': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'State': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.linkedfacebookaccount': {
            'AccessToken': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'ExpiresIn': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'Meta': {'object_name': 'LinkedFacebookAccount'},
            'facebook_id': ('django.db.models.fields.CharField', [], {'max_length': '24', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'linked_facebook'", 'unique': 'True', 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.linkedgoogleaccount': {
            'Meta': {'object_name': 'LinkedGoogleAccount'},
            'credentials_json': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'gplus_id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'linked_gplus'", 'unique': 'True', 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.listen': {
            'Meta': {'unique_together': "(('listener', 'stream'),)", 'object_name': 'Listen'},
            'date_listened': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'listener': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.Stream2']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.message': {
            'Conversation': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Messages'", 'to': "orm['shoutit.Conversation']"}),
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'FromUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'received_messages'", 'to': u"orm['auth.User']"}),
            'IsRead': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Message'},
            'Text': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'ToUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent_messages'", 'to': u"orm['auth.User']"}),
            'VisibleToRecivier': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'VisibleToSender': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.messageattachment': {
            'Meta': {'object_name': 'MessageAttachment'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['shoutit.Message']"}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.notification': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'FromUser': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'+'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'IsRead': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Notification'},
            'ToUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Notifications'", 'to': u"orm['auth.User']"}),
            'Type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'object_pk': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.payment': {
            'Amount': ('django.db.models.fields.FloatField', [], {}),
            'Currency': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['shoutit.Currency']"}),
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'DateUpdated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'Payment'},
            'Status': ('django.db.models.fields.IntegerField', [], {}),
            'Transaction': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Payment'", 'to': "orm['shoutit.Transaction']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'object_pk': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Payments'", 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.permission': {
            'Meta': {'object_name': 'Permission'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512', 'db_index': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'permissions'", 'symmetrical': 'False', 'through': "orm['shoutit.UserPermission']", 'to': u"orm['auth.User']"})
        },
        'shoutit.post': {
            'Address': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'db_index': 'True'}),
            'CountryCode': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'db_index': 'True'}),
            'DatePublished': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'IsDisabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'IsMuted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'Latitude': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'Longitude': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'Meta': {'object_name': 'Post'},
            'OwnerUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Posts'", 'to': u"orm['auth.User']"}),
            'ProvinceCode': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'db_index': 'True'}),
            'Streams': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'Posts'", 'symmetrical': 'False', 'to': "orm['shoutit.Stream']"}),
            'Text': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '2000', 'db_index': 'True'}),
            'Type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.predefinedcity': {
            'Approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'City': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'Country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2', 'db_index': 'True'}),
            'EncodedCity': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'Latitude': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'Longitude': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'Meta': {'object_name': 'PredefinedCity'},
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.profile': {
            'Bio': ('django.db.models.fields.TextField', [], {'default': "'New Shouter!'", 'max_length': '512', 'null': 'True'}),
            'City': ('django.db.models.fields.CharField', [], {'default': "'Dubai'", 'max_length': '200', 'db_index': 'True'}),
            'Country': ('django.db.models.fields.CharField', [], {'default': "'AE'", 'max_length': '200', 'db_index': 'True'}),
            'Following': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['shoutit.Stream']", 'through': "orm['shoutit.FollowShip']", 'symmetrical': 'False'}),
            'Image': ('django.db.models.fields.URLField', [], {'max_length': '1024', 'null': 'True'}),
            'Interests': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'Followers'", 'symmetrical': 'False', 'to': "orm['shoutit.Tag']"}),
            'LastToken': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['shoutit.ConfirmToken']", 'null': 'True', 'on_delete': 'models.SET_NULL'}),
            'Latitude': ('django.db.models.fields.FloatField', [], {'default': '25.1993957'}),
            'Longitude': ('django.db.models.fields.FloatField', [], {'default': '55.2738326'}),
            'Meta': {'object_name': 'Profile'},
            'Mobile': ('django.db.models.fields.CharField', [], {'max_length': '20', 'unique': 'True', 'null': 'True'}),
            'Sex': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'Stream': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'OwnerUser'", 'unique': 'True', 'to': "orm['shoutit.Stream']"}),
            'birthday': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'isSMS': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'isSSS': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'null': 'True', 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.report': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'IsDisabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'IsSolved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Report'},
            'Text': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '300'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'object_pk': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Reports'", 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.service': {
            'Code': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'Meta': {'object_name': 'Service'},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'Price': ('django.db.models.fields.FloatField', [], {}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.servicebuy': {
            'Amount': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'DateBought': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'ServiceBuy'},
            'Service': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Buyers'", 'to': "orm['shoutit.Service']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Services'", 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.serviceusage': {
            'Amount': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'DateUsed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'ServiceUsage'},
            'Service': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'BuyersUsages'", 'to': "orm['shoutit.Service']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ServicesUsages'", 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.sharedexperience': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Experience': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'SharedExperiences'", 'to': "orm['shoutit.Experience']"}),
            'Meta': {'unique_together': "(('Experience', 'OwnerUser'),)", 'object_name': 'SharedExperience'},
            'OwnerUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'SharedExperiences'", 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.shout': {
            'ExpiryDate': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'db_index': 'True'}),
            'ExpiryNotified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Shout', '_ormbases': ['shoutit.Post']},
            'Tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'Shouts'", 'symmetrical': 'False', 'to': "orm['shoutit.Tag']"}),
            u'post_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['shoutit.Post']", 'unique': 'True', 'primary_key': 'True'})
        },
        'shoutit.shoutwrap': {
            'Meta': {'object_name': 'ShoutWrap'},
            'Rank': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'Shout': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ShoutWraps'", 'to': "orm['shoutit.Shout']"}),
            'Stream': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ShoutWraps'", 'to': "orm['shoutit.Stream']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.storedfile': {
            'File': ('django.db.models.fields.URLField', [], {'max_length': '1024'}),
            'Meta': {'object_name': 'StoredFile'},
            'Type': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Documents'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.storedimage': {
            'Image': ('django.db.models.fields.URLField', [], {'max_length': '1024'}),
            'Item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Images'", 'null': 'True', 'to': "orm['shoutit.Item']"}),
            'Meta': {'object_name': 'StoredImage'},
            'Shout': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Images'", 'null': 'True', 'to': "orm['shoutit.Shout']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.stream': {
            'Meta': {'object_name': 'Stream'},
            'Type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.stream2': {
            'Meta': {'unique_together': "(('content_type', 'object_uuid', 'type'),)", 'object_name': 'Stream2'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'listeners': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'listening'", 'symmetrical': 'False', 'through': "orm['shoutit.Listen']", 'to': u"orm['auth.User']"}),
            'object_uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'blank': 'True'}),
            'posts': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'streams'", 'symmetrical': 'False', 'to': "orm['shoutit.Post']"}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.subscription': {
            'DeactivateDate': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'Meta': {'object_name': 'Subscription'},
            'Password': ('django.db.models.fields.CharField', [], {'max_length': '24'}),
            'SignUpDate': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'State': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'UserName': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.tag': {
            'Creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'TagsCreated'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['auth.User']"}),
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Definition': ('django.db.models.fields.TextField', [], {'default': "'New Tag!'", 'max_length': '512', 'null': 'True'}),
            'Image': ('django.db.models.fields.URLField', [], {'default': "'/static/img/shout_tag.png'", 'max_length': '1024', 'null': 'True'}),
            'Meta': {'object_name': 'Tag'},
            'Name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'Parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ChildTags'", 'null': 'True', 'to': "orm['shoutit.Tag']"}),
            'Stream': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'OwnerTag'", 'unique': 'True', 'null': 'True', 'to': "orm['shoutit.Stream']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.trade': {
            'BaseDatePublished': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'IsSSS': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'IsShowMobile': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'Item': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'Shout'", 'unique': 'True', 'null': 'True', 'to': "orm['shoutit.Item']"}),
            'MaxDistance': ('django.db.models.fields.FloatField', [], {'default': '180.0'}),
            'MaxFollowings': ('django.db.models.fields.IntegerField', [], {'default': '6'}),
            'MaxPrice': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'Meta': {'object_name': 'Trade', '_ormbases': ['shoutit.Shout']},
            'RecommendedStream': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'InitShoutRecommended'", 'unique': 'True', 'null': 'True', 'to': "orm['shoutit.Stream']"}),
            'RelatedStream': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'InitShoutRelated'", 'unique': 'True', 'null': 'True', 'to': "orm['shoutit.Stream']"}),
            'RenewalCount': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'StreamsCode': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2000'}),
            u'shout_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['shoutit.Shout']", 'unique': 'True', 'primary_key': 'True'})
        },
        'shoutit.transaction': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'DateUpdated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'Transaction'},
            'RemoteData': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'RemoteIdentifier': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'RemoteStatus': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.userpermission': {
            'Meta': {'object_name': 'UserPermission'},
            'date_given': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'permission': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.Permission']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.video': {
            'Meta': {'object_name': 'Video'},
            'duration': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id_on_provider': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'videos'", 'null': 'True', 'to': "orm['shoutit.Item']"}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'shout': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'videos'", 'null': 'True', 'to': "orm['shoutit.Shout']"}),
            'thumbnail_url': ('django.db.models.fields.URLField', [], {'max_length': '1024'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1024'}),
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        },
        'shoutit.voucher': {
            'Code': ('django.db.models.fields.CharField', [], {'max_length': '22'}),
            'DateGenerated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'DealBuy': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Vouchers'", 'to': "orm['shoutit.DealBuy']"}),
            'IsSent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'IsValidated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Voucher'},
            'uuid': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '36', 'primary_key': 'True'})
        }
    }

    complete_apps = ['shoutit']