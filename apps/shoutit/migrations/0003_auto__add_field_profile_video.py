# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Profile.video'
        db.add_column(u'shoutit_profile', 'video',
                      self.gf('django.db.models.fields.related.OneToOneField')(to=orm['shoutit.Video'], unique=True, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Profile.video'
        db.delete_column(u'shoutit_profile', 'video_id')


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
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'business'", 'unique': 'True', 'to': u"orm['shoutit.User']"})
        },
        'shoutit.businesscategory': {
            'Meta': {'object_name': 'BusinessCategory'},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'db_index': 'True'}),
            'Parent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'children'", 'null': 'True', 'to': "orm['shoutit.BusinessCategory']"}),
            'Source': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'SourceID': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.businessconfirmation': {
            'DateSent': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Files': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'Confirmation'", 'symmetrical': 'False', 'to': "orm['shoutit.StoredFile']"}),
            'Meta': {'object_name': 'BusinessConfirmation'},
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'BusinessConfirmations'", 'to': u"orm['shoutit.User']"})
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
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'BusinessCreateApplication'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['shoutit.User']"})
        },
        'shoutit.businesssource': {
            'Meta': {'object_name': 'BusinessSource'},
            'Source': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'SourceID': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'business': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'Source'", 'unique': 'True', 'to': "orm['shoutit.Business']"}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.category': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'Category'},
            'Name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'Tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'Category'", 'symmetrical': 'False', 'to': "orm['shoutit.Tag']"}),
            'TopTag': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'OwnerCategory'", 'unique': 'True', 'null': 'True', 'to': "orm['shoutit.Tag']"}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.comment': {
            'AboutPost': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Comments'", 'null': 'True', 'to': "orm['shoutit.Post']"}),
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'IsDisabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Comment'},
            'OwnerUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['shoutit.User']"}),
            'Text': ('django.db.models.fields.TextField', [], {'max_length': '300'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.confirmtoken': {
            'DateCreated': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Email': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'IsDisabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'ConfirmToken'},
            'Token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '24', 'db_index': 'True'}),
            'Type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Tokens'", 'to': u"orm['shoutit.User']"})
        },
        'shoutit.conversation': {
            'AboutPost': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['shoutit.Trade']"}),
            'FromUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['shoutit.User']"}),
            'IsRead': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Conversation'},
            'ToUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['shoutit.User']"}),
            'VisibleToRecivier': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'VisibleToSender': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.currency': {
            'Code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'Country': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'Meta': {'object_name': 'Currency'},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
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
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'DealsBought'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['shoutit.User']"})
        },
        'shoutit.event': {
            'EventType': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Meta': {'object_name': 'Event', '_ormbases': ['shoutit.Post']},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'object_id': ('uuidfield.fields.UUIDField', [], {'max_length': '32', 'null': 'True'}),
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
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Contest_1'", 'to': u"orm['shoutit.User']"})
        },
        'shoutit.followship': {
            'Meta': {'object_name': 'FollowShip'},
            'date_followed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'follower': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.Profile']"}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.Stream']"})
        },
        'shoutit.gallery': {
            'Category': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'to': "orm['shoutit.Category']"}),
            'Description': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '500'}),
            'Meta': {'object_name': 'Gallery'},
            'OwnerBusiness': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Galleries'", 'to': "orm['shoutit.Business']"}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.galleryitem': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Gallery': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'GalleryItems'", 'to': "orm['shoutit.Gallery']"}),
            'IsDisable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'IsMuted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['shoutit.Item']"}),
            'Meta': {'unique_together': "(('Item', 'Gallery'),)", 'object_name': 'GalleryItem'},
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.item': {
            'Currency': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Items'", 'to': "orm['shoutit.Currency']"}),
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000'}),
            'Meta': {'object_name': 'Item'},
            'Name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512'}),
            'Price': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'State': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.linkedfacebookaccount': {
            'AccessToken': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'ExpiresIn': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'Meta': {'object_name': 'LinkedFacebookAccount'},
            'facebook_id': ('django.db.models.fields.CharField', [], {'max_length': '24', 'db_index': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'linked_facebook'", 'unique': 'True', 'to': u"orm['shoutit.User']"})
        },
        'shoutit.linkedgoogleaccount': {
            'Meta': {'object_name': 'LinkedGoogleAccount'},
            'credentials_json': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'gplus_id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'linked_gplus'", 'unique': 'True', 'to': u"orm['shoutit.User']"})
        },
        'shoutit.listen': {
            'Meta': {'unique_together': "(('listener', 'stream'),)", 'object_name': 'Listen'},
            'date_listened': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'listener': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shoutit.User']"}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.Stream2']"})
        },
        'shoutit.message': {
            'Conversation': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Messages'", 'to': "orm['shoutit.Conversation']"}),
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'FromUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'received_messages'", 'to': u"orm['shoutit.User']"}),
            'IsRead': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Message'},
            'Text': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'ToUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent_messages'", 'to': u"orm['shoutit.User']"}),
            'VisibleToRecivier': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'VisibleToSender': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.messageattachment': {
            'Meta': {'object_name': 'MessageAttachment'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['shoutit.Message']"}),
            'object_id': ('uuidfield.fields.UUIDField', [], {'max_length': '32', 'null': 'True'})
        },
        'shoutit.notification': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'FromUser': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'+'", 'null': 'True', 'to': u"orm['shoutit.User']"}),
            'IsRead': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Notification'},
            'ToUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Notifications'", 'to': u"orm['shoutit.User']"}),
            'Type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'object_id': ('uuidfield.fields.UUIDField', [], {'max_length': '32', 'null': 'True'})
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
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'object_id': ('uuidfield.fields.UUIDField', [], {'max_length': '32', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Payments'", 'to': u"orm['shoutit.User']"})
        },
        'shoutit.permission': {
            'Meta': {'object_name': 'Permission'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512', 'db_index': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'permissions'", 'symmetrical': 'False', 'through': "orm['shoutit.UserPermission']", 'to': u"orm['shoutit.User']"})
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
            'OwnerUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Posts'", 'to': u"orm['shoutit.User']"}),
            'ProvinceCode': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'db_index': 'True'}),
            'Streams': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'Posts'", 'symmetrical': 'False', 'to': "orm['shoutit.Stream']"}),
            'Text': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '2000', 'db_index': 'True'}),
            'Type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.predefinedcity': {
            'Approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'City': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'Country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2', 'db_index': 'True'}),
            'Latitude': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'Longitude': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'Meta': {'object_name': 'PredefinedCity'},
            'city_encoded': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
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
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'isSMS': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'isSSS': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'null': 'True', 'to': u"orm['shoutit.User']"}),
            'video': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['shoutit.Video']", 'unique': 'True', 'null': 'True'})
        },
        'shoutit.report': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'IsDisabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'IsSolved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Report'},
            'Text': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '300'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'object_id': ('uuidfield.fields.UUIDField', [], {'max_length': '32', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Reports'", 'to': u"orm['shoutit.User']"})
        },
        'shoutit.service': {
            'Code': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'Meta': {'object_name': 'Service'},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'Price': ('django.db.models.fields.FloatField', [], {}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.servicebuy': {
            'Amount': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'DateBought': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'ServiceBuy'},
            'Service': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Buyers'", 'to': "orm['shoutit.Service']"}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Services'", 'to': u"orm['shoutit.User']"})
        },
        'shoutit.serviceusage': {
            'Amount': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'DateUsed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'ServiceUsage'},
            'Service': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'BuyersUsages'", 'to': "orm['shoutit.Service']"}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ServicesUsages'", 'to': u"orm['shoutit.User']"})
        },
        'shoutit.sharedexperience': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Experience': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'SharedExperiences'", 'to': "orm['shoutit.Experience']"}),
            'Meta': {'unique_together': "(('Experience', 'OwnerUser'),)", 'object_name': 'SharedExperience'},
            'OwnerUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'SharedExperiences'", 'to': u"orm['shoutit.User']"}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
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
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.storedfile': {
            'File': ('django.db.models.fields.URLField', [], {'max_length': '1024'}),
            'Meta': {'object_name': 'StoredFile'},
            'Type': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Documents'", 'null': 'True', 'to': u"orm['shoutit.User']"})
        },
        'shoutit.storedimage': {
            'Image': ('django.db.models.fields.URLField', [], {'max_length': '1024'}),
            'Item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Images'", 'null': 'True', 'to': "orm['shoutit.Item']"}),
            'Meta': {'object_name': 'StoredImage'},
            'Shout': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Images'", 'null': 'True', 'to': "orm['shoutit.Shout']"}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.stream': {
            'Meta': {'object_name': 'Stream'},
            'Type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.stream2': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'type'),)", 'object_name': 'Stream2'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'listeners': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'listening'", 'symmetrical': 'False', 'through': "orm['shoutit.Listen']", 'to': u"orm['shoutit.User']"}),
            'object_id': ('uuidfield.fields.UUIDField', [], {'max_length': '32', 'null': 'True'}),
            'posts': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'streams2'", 'symmetrical': 'False', 'to': "orm['shoutit.Post']"}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True'})
        },
        'shoutit.subscription': {
            'DeactivateDate': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'Meta': {'object_name': 'Subscription'},
            'Password': ('django.db.models.fields.CharField', [], {'max_length': '24'}),
            'SignUpDate': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'State': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'Type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'UserName': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        'shoutit.tag': {
            'Creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'TagsCreated'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['shoutit.User']"}),
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Definition': ('django.db.models.fields.TextField', [], {'default': "'New Tag!'", 'max_length': '512', 'null': 'True'}),
            'Image': ('django.db.models.fields.URLField', [], {'default': "'/static/img/shout_tag.png'", 'max_length': '1024', 'null': 'True'}),
            'Meta': {'object_name': 'Tag'},
            'Name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'Parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ChildTags'", 'null': 'True', 'to': "orm['shoutit.Tag']"}),
            'Stream': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'OwnerTag'", 'unique': 'True', 'null': 'True', 'to': "orm['shoutit.Stream']"}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
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
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        },
        u'shoutit.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'shoutit.userpermission': {
            'Meta': {'object_name': 'UserPermission'},
            'date_given': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'permission': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.Permission']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shoutit.User']"})
        },
        'shoutit.video': {
            'Meta': {'object_name': 'Video'},
            'duration': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'id_on_provider': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'videos'", 'null': 'True', 'to': "orm['shoutit.Item']"}),
            'provider': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'shout': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'videos'", 'null': 'True', 'to': "orm['shoutit.Shout']"}),
            'thumbnail_url': ('django.db.models.fields.URLField', [], {'max_length': '1024'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '1024'})
        },
        'shoutit.voucher': {
            'Code': ('django.db.models.fields.CharField', [], {'max_length': '22'}),
            'DateGenerated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'DealBuy': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Vouchers'", 'to': "orm['shoutit.DealBuy']"}),
            'IsSent': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'IsValidated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Voucher'},
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'})
        }
    }

    complete_apps = ['shoutit']