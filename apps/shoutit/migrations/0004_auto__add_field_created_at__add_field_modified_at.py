# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Business.created_at'
        db.add_column(u'shoutit_business', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Business.modified_at'
        db.add_column(u'shoutit_business', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FbContest.created_at'
        db.add_column(u'shoutit_fbcontest', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FbContest.modified_at'
        db.add_column(u'shoutit_fbcontest', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Message.created_at'
        db.add_column(u'shoutit_message', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Message.modified_at'
        db.add_column(u'shoutit_message', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Video.created_at'
        db.add_column(u'shoutit_video', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Video.modified_at'
        db.add_column(u'shoutit_video', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ServiceUsage.created_at'
        db.add_column(u'shoutit_serviceusage', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ServiceUsage.modified_at'
        db.add_column(u'shoutit_serviceusage', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Report.created_at'
        db.add_column(u'shoutit_report', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Report.modified_at'
        db.add_column(u'shoutit_report', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Transaction.created_at'
        db.add_column(u'shoutit_transaction', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Transaction.modified_at'
        db.add_column(u'shoutit_transaction', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Currency.created_at'
        db.add_column(u'shoutit_currency', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Currency.modified_at'
        db.add_column(u'shoutit_currency', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'StoredImage.created_at'
        db.add_column(u'shoutit_storedimage', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'StoredImage.modified_at'
        db.add_column(u'shoutit_storedimage', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Category.created_at'
        db.add_column(u'shoutit_category', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Category.modified_at'
        db.add_column(u'shoutit_category', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'DealBuy.created_at'
        db.add_column(u'shoutit_dealbuy', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'DealBuy.modified_at'
        db.add_column(u'shoutit_dealbuy', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'BusinessConfirmation.created_at'
        db.add_column(u'shoutit_businessconfirmation', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'BusinessConfirmation.modified_at'
        db.add_column(u'shoutit_businessconfirmation', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Stream2.created_at'
        db.add_column(u'shoutit_stream2', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Stream2.modified_at'
        db.add_column(u'shoutit_stream2', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Subscription.created_at'
        db.add_column(u'shoutit_subscription', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Subscription.modified_at'
        db.add_column(u'shoutit_subscription', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Notification.created_at'
        db.add_column(u'shoutit_notification', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Notification.modified_at'
        db.add_column(u'shoutit_notification', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'StoredFile.created_at'
        db.add_column(u'shoutit_storedfile', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'StoredFile.modified_at'
        db.add_column(u'shoutit_storedfile', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Tag.created_at'
        db.add_column(u'shoutit_tag', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Tag.modified_at'
        db.add_column(u'shoutit_tag', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Payment.created_at'
        db.add_column(u'shoutit_payment', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Payment.modified_at'
        db.add_column(u'shoutit_payment', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'BusinessSource.created_at'
        db.add_column(u'shoutit_businesssource', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'BusinessSource.modified_at'
        db.add_column(u'shoutit_businesssource', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Comment.created_at'
        db.add_column(u'shoutit_comment', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Comment.modified_at'
        db.add_column(u'shoutit_comment', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'PredefinedCity.created_at'
        db.add_column(u'shoutit_predefinedcity', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'PredefinedCity.modified_at'
        db.add_column(u'shoutit_predefinedcity', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Post.created_at'
        db.add_column(u'shoutit_post', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Post.modified_at'
        db.add_column(u'shoutit_post', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'GalleryItem.created_at'
        db.add_column(u'shoutit_galleryitem', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'GalleryItem.modified_at'
        db.add_column(u'shoutit_galleryitem', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'BusinessCreateApplication.created_at'
        db.add_column(u'shoutit_businesscreateapplication', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'BusinessCreateApplication.modified_at'
        db.add_column(u'shoutit_businesscreateapplication', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'BusinessCategory.created_at'
        db.add_column(u'shoutit_businesscategory', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'BusinessCategory.modified_at'
        db.add_column(u'shoutit_businesscategory', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'LinkedGoogleAccount.created_at'
        db.add_column(u'shoutit_linkedgoogleaccount', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'LinkedGoogleAccount.modified_at'
        db.add_column(u'shoutit_linkedgoogleaccount', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'LinkedFacebookAccount.created_at'
        db.add_column(u'shoutit_linkedfacebookaccount', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'LinkedFacebookAccount.modified_at'
        db.add_column(u'shoutit_linkedfacebookaccount', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'MessageAttachment.created_at'
        db.add_column(u'shoutit_messageattachment', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'MessageAttachment.modified_at'
        db.add_column(u'shoutit_messageattachment', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Item.created_at'
        db.add_column(u'shoutit_item', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Item.modified_at'
        db.add_column(u'shoutit_item', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Listen.created_at'
        db.add_column(u'shoutit_listen', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Listen.modified_at'
        db.add_column(u'shoutit_listen', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Stream.created_at'
        db.add_column(u'shoutit_stream', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Stream.modified_at'
        db.add_column(u'shoutit_stream', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Gallery.created_at'
        db.add_column(u'shoutit_gallery', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Gallery.modified_at'
        db.add_column(u'shoutit_gallery', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Service.created_at'
        db.add_column(u'shoutit_service', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Service.modified_at'
        db.add_column(u'shoutit_service', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ConfirmToken.created_at'
        db.add_column(u'shoutit_confirmtoken', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ConfirmToken.modified_at'
        db.add_column(u'shoutit_confirmtoken', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FollowShip.created_at'
        db.add_column(u'shoutit_followship', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FollowShip.modified_at'
        db.add_column(u'shoutit_followship', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Profile.created_at'
        db.add_column(u'shoutit_profile', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Profile.modified_at'
        db.add_column(u'shoutit_profile', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'User.created_at'
        db.add_column(u'shoutit_user', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'User.modified_at'
        db.add_column(u'shoutit_user', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserPermission.created_at'
        db.add_column(u'shoutit_userpermission', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'UserPermission.modified_at'
        db.add_column(u'shoutit_userpermission', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ServiceBuy.created_at'
        db.add_column(u'shoutit_servicebuy', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ServiceBuy.modified_at'
        db.add_column(u'shoutit_servicebuy', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ShoutWrap.created_at'
        db.add_column(u'shoutit_shoutwrap', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ShoutWrap.modified_at'
        db.add_column(u'shoutit_shoutwrap', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Voucher.created_at'
        db.add_column(u'shoutit_voucher', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Voucher.modified_at'
        db.add_column(u'shoutit_voucher', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'SharedExperience.created_at'
        db.add_column(u'shoutit_sharedexperience', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'SharedExperience.modified_at'
        db.add_column(u'shoutit_sharedexperience', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Conversation.created_at'
        db.add_column(u'shoutit_conversation', 'created_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Conversation.modified_at'
        db.add_column(u'shoutit_conversation', 'modified_at',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Business.created_at'
        db.delete_column(u'shoutit_business', 'created_at')

        # Deleting field 'Business.modified_at'
        db.delete_column(u'shoutit_business', 'modified_at')

        # Deleting field 'FbContest.created_at'
        db.delete_column(u'shoutit_fbcontest', 'created_at')

        # Deleting field 'FbContest.modified_at'
        db.delete_column(u'shoutit_fbcontest', 'modified_at')

        # Deleting field 'Message.created_at'
        db.delete_column(u'shoutit_message', 'created_at')

        # Deleting field 'Message.modified_at'
        db.delete_column(u'shoutit_message', 'modified_at')

        # Deleting field 'Video.created_at'
        db.delete_column(u'shoutit_video', 'created_at')

        # Deleting field 'Video.modified_at'
        db.delete_column(u'shoutit_video', 'modified_at')

        # Deleting field 'ServiceUsage.created_at'
        db.delete_column(u'shoutit_serviceusage', 'created_at')

        # Deleting field 'ServiceUsage.modified_at'
        db.delete_column(u'shoutit_serviceusage', 'modified_at')

        # Deleting field 'Report.created_at'
        db.delete_column(u'shoutit_report', 'created_at')

        # Deleting field 'Report.modified_at'
        db.delete_column(u'shoutit_report', 'modified_at')

        # Deleting field 'Transaction.created_at'
        db.delete_column(u'shoutit_transaction', 'created_at')

        # Deleting field 'Transaction.modified_at'
        db.delete_column(u'shoutit_transaction', 'modified_at')

        # Deleting field 'Currency.created_at'
        db.delete_column(u'shoutit_currency', 'created_at')

        # Deleting field 'Currency.modified_at'
        db.delete_column(u'shoutit_currency', 'modified_at')

        # Deleting field 'StoredImage.created_at'
        db.delete_column(u'shoutit_storedimage', 'created_at')

        # Deleting field 'StoredImage.modified_at'
        db.delete_column(u'shoutit_storedimage', 'modified_at')

        # Deleting field 'Category.created_at'
        db.delete_column(u'shoutit_category', 'created_at')

        # Deleting field 'Category.modified_at'
        db.delete_column(u'shoutit_category', 'modified_at')

        # Deleting field 'DealBuy.created_at'
        db.delete_column(u'shoutit_dealbuy', 'created_at')

        # Deleting field 'DealBuy.modified_at'
        db.delete_column(u'shoutit_dealbuy', 'modified_at')

        # Deleting field 'BusinessConfirmation.created_at'
        db.delete_column(u'shoutit_businessconfirmation', 'created_at')

        # Deleting field 'BusinessConfirmation.modified_at'
        db.delete_column(u'shoutit_businessconfirmation', 'modified_at')

        # Deleting field 'Stream2.created_at'
        db.delete_column(u'shoutit_stream2', 'created_at')

        # Deleting field 'Stream2.modified_at'
        db.delete_column(u'shoutit_stream2', 'modified_at')

        # Deleting field 'Subscription.created_at'
        db.delete_column(u'shoutit_subscription', 'created_at')

        # Deleting field 'Subscription.modified_at'
        db.delete_column(u'shoutit_subscription', 'modified_at')

        # Deleting field 'Notification.created_at'
        db.delete_column(u'shoutit_notification', 'created_at')

        # Deleting field 'Notification.modified_at'
        db.delete_column(u'shoutit_notification', 'modified_at')

        # Deleting field 'StoredFile.created_at'
        db.delete_column(u'shoutit_storedfile', 'created_at')

        # Deleting field 'StoredFile.modified_at'
        db.delete_column(u'shoutit_storedfile', 'modified_at')

        # Deleting field 'Tag.created_at'
        db.delete_column(u'shoutit_tag', 'created_at')

        # Deleting field 'Tag.modified_at'
        db.delete_column(u'shoutit_tag', 'modified_at')

        # Deleting field 'Payment.created_at'
        db.delete_column(u'shoutit_payment', 'created_at')

        # Deleting field 'Payment.modified_at'
        db.delete_column(u'shoutit_payment', 'modified_at')

        # Deleting field 'BusinessSource.created_at'
        db.delete_column(u'shoutit_businesssource', 'created_at')

        # Deleting field 'BusinessSource.modified_at'
        db.delete_column(u'shoutit_businesssource', 'modified_at')

        # Deleting field 'Comment.created_at'
        db.delete_column(u'shoutit_comment', 'created_at')

        # Deleting field 'Comment.modified_at'
        db.delete_column(u'shoutit_comment', 'modified_at')

        # Deleting field 'PredefinedCity.created_at'
        db.delete_column(u'shoutit_predefinedcity', 'created_at')

        # Deleting field 'PredefinedCity.modified_at'
        db.delete_column(u'shoutit_predefinedcity', 'modified_at')

        # Deleting field 'Post.created_at'
        db.delete_column(u'shoutit_post', 'created_at')

        # Deleting field 'Post.modified_at'
        db.delete_column(u'shoutit_post', 'modified_at')

        # Deleting field 'GalleryItem.created_at'
        db.delete_column(u'shoutit_galleryitem', 'created_at')

        # Deleting field 'GalleryItem.modified_at'
        db.delete_column(u'shoutit_galleryitem', 'modified_at')

        # Deleting field 'BusinessCreateApplication.created_at'
        db.delete_column(u'shoutit_businesscreateapplication', 'created_at')

        # Deleting field 'BusinessCreateApplication.modified_at'
        db.delete_column(u'shoutit_businesscreateapplication', 'modified_at')

        # Deleting field 'BusinessCategory.created_at'
        db.delete_column(u'shoutit_businesscategory', 'created_at')

        # Deleting field 'BusinessCategory.modified_at'
        db.delete_column(u'shoutit_businesscategory', 'modified_at')

        # Deleting field 'LinkedGoogleAccount.created_at'
        db.delete_column(u'shoutit_linkedgoogleaccount', 'created_at')

        # Deleting field 'LinkedGoogleAccount.modified_at'
        db.delete_column(u'shoutit_linkedgoogleaccount', 'modified_at')

        # Deleting field 'LinkedFacebookAccount.created_at'
        db.delete_column(u'shoutit_linkedfacebookaccount', 'created_at')

        # Deleting field 'LinkedFacebookAccount.modified_at'
        db.delete_column(u'shoutit_linkedfacebookaccount', 'modified_at')

        # Deleting field 'MessageAttachment.created_at'
        db.delete_column(u'shoutit_messageattachment', 'created_at')

        # Deleting field 'MessageAttachment.modified_at'
        db.delete_column(u'shoutit_messageattachment', 'modified_at')

        # Deleting field 'Item.created_at'
        db.delete_column(u'shoutit_item', 'created_at')

        # Deleting field 'Item.modified_at'
        db.delete_column(u'shoutit_item', 'modified_at')

        # Deleting field 'Listen.created_at'
        db.delete_column(u'shoutit_listen', 'created_at')

        # Deleting field 'Listen.modified_at'
        db.delete_column(u'shoutit_listen', 'modified_at')

        # Deleting field 'Stream.created_at'
        db.delete_column(u'shoutit_stream', 'created_at')

        # Deleting field 'Stream.modified_at'
        db.delete_column(u'shoutit_stream', 'modified_at')

        # Deleting field 'Gallery.created_at'
        db.delete_column(u'shoutit_gallery', 'created_at')

        # Deleting field 'Gallery.modified_at'
        db.delete_column(u'shoutit_gallery', 'modified_at')

        # Deleting field 'Service.created_at'
        db.delete_column(u'shoutit_service', 'created_at')

        # Deleting field 'Service.modified_at'
        db.delete_column(u'shoutit_service', 'modified_at')

        # Deleting field 'ConfirmToken.created_at'
        db.delete_column(u'shoutit_confirmtoken', 'created_at')

        # Deleting field 'ConfirmToken.modified_at'
        db.delete_column(u'shoutit_confirmtoken', 'modified_at')

        # Deleting field 'FollowShip.created_at'
        db.delete_column(u'shoutit_followship', 'created_at')

        # Deleting field 'FollowShip.modified_at'
        db.delete_column(u'shoutit_followship', 'modified_at')

        # Deleting field 'Profile.created_at'
        db.delete_column(u'shoutit_profile', 'created_at')

        # Deleting field 'Profile.modified_at'
        db.delete_column(u'shoutit_profile', 'modified_at')

        # Deleting field 'User.created_at'
        db.delete_column(u'shoutit_user', 'created_at')

        # Deleting field 'User.modified_at'
        db.delete_column(u'shoutit_user', 'modified_at')

        # Deleting field 'UserPermission.created_at'
        db.delete_column(u'shoutit_userpermission', 'created_at')

        # Deleting field 'UserPermission.modified_at'
        db.delete_column(u'shoutit_userpermission', 'modified_at')

        # Deleting field 'ServiceBuy.created_at'
        db.delete_column(u'shoutit_servicebuy', 'created_at')

        # Deleting field 'ServiceBuy.modified_at'
        db.delete_column(u'shoutit_servicebuy', 'modified_at')

        # Deleting field 'ShoutWrap.created_at'
        db.delete_column(u'shoutit_shoutwrap', 'created_at')

        # Deleting field 'ShoutWrap.modified_at'
        db.delete_column(u'shoutit_shoutwrap', 'modified_at')

        # Deleting field 'Voucher.created_at'
        db.delete_column(u'shoutit_voucher', 'created_at')

        # Deleting field 'Voucher.modified_at'
        db.delete_column(u'shoutit_voucher', 'modified_at')

        # Deleting field 'SharedExperience.created_at'
        db.delete_column(u'shoutit_sharedexperience', 'created_at')

        # Deleting field 'SharedExperience.modified_at'
        db.delete_column(u'shoutit_sharedexperience', 'modified_at')

        # Deleting field 'Conversation.created_at'
        db.delete_column(u'shoutit_conversation', 'created_at')

        # Deleting field 'Conversation.modified_at'
        db.delete_column(u'shoutit_conversation', 'modified_at')


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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'business'", 'unique': 'True', 'to': u"orm['shoutit.User']"})
        },
        'shoutit.businesscategory': {
            'Meta': {'object_name': 'BusinessCategory'},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'db_index': 'True'}),
            'Parent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'children'", 'null': 'True', 'to': "orm['shoutit.BusinessCategory']"}),
            'Source': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'SourceID': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.businessconfirmation': {
            'DateSent': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Files': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'Confirmation'", 'symmetrical': 'False', 'to': "orm['shoutit.StoredFile']"}),
            'Meta': {'object_name': 'BusinessConfirmation'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'BusinessCreateApplication'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': u"orm['shoutit.User']"})
        },
        'shoutit.businesssource': {
            'Meta': {'object_name': 'BusinessSource'},
            'Source': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'SourceID': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'business': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'Source'", 'unique': 'True', 'to': "orm['shoutit.Business']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.category': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'Category'},
            'Name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'Tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'Category'", 'symmetrical': 'False', 'to': "orm['shoutit.Tag']"}),
            'TopTag': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'OwnerCategory'", 'unique': 'True', 'null': 'True', 'to': "orm['shoutit.Tag']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.comment': {
            'AboutPost': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Comments'", 'null': 'True', 'to': "orm['shoutit.Post']"}),
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'IsDisabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Comment'},
            'OwnerUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['shoutit.User']"}),
            'Text': ('django.db.models.fields.TextField', [], {'max_length': '300'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.confirmtoken': {
            'DateCreated': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Email': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'IsDisabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'ConfirmToken'},
            'Token': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '24', 'db_index': 'True'}),
            'Type': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.currency': {
            'Code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'Country': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'Meta': {'object_name': 'Currency'},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Contest_1'", 'to': u"orm['shoutit.User']"})
        },
        'shoutit.followship': {
            'Meta': {'object_name': 'FollowShip'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'date_followed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'follower': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.Profile']"}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'stream': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.Stream']"})
        },
        'shoutit.gallery': {
            'Category': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'+'", 'unique': 'True', 'null': 'True', 'to': "orm['shoutit.Category']"}),
            'Description': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '500'}),
            'Meta': {'object_name': 'Gallery'},
            'OwnerBusiness': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Galleries'", 'to': "orm['shoutit.Business']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.galleryitem': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Gallery': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'GalleryItems'", 'to': "orm['shoutit.Gallery']"}),
            'IsDisable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'IsMuted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['shoutit.Item']"}),
            'Meta': {'unique_together': "(('Item', 'Gallery'),)", 'object_name': 'GalleryItem'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.item': {
            'Currency': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Items'", 'to': "orm['shoutit.Currency']"}),
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000'}),
            'Meta': {'object_name': 'Item'},
            'Name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '512'}),
            'Price': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'State': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.linkedfacebookaccount': {
            'AccessToken': ('django.db.models.fields.CharField', [], {'max_length': '512'}),
            'ExpiresIn': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'Meta': {'object_name': 'LinkedFacebookAccount'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'facebook_id': ('django.db.models.fields.CharField', [], {'max_length': '24', 'db_index': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'linked_facebook'", 'unique': 'True', 'to': u"orm['shoutit.User']"})
        },
        'shoutit.linkedgoogleaccount': {
            'Meta': {'object_name': 'LinkedGoogleAccount'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'credentials_json': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'gplus_id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'linked_gplus'", 'unique': 'True', 'to': u"orm['shoutit.User']"})
        },
        'shoutit.listen': {
            'Meta': {'unique_together': "(('listener', 'stream'),)", 'object_name': 'Listen'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'date_listened': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'listener': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shoutit.User']"}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.messageattachment': {
            'Meta': {'object_name': 'MessageAttachment'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'attachments'", 'to': "orm['shoutit.Message']"}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.predefinedcity': {
            'Approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'City': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'Country': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2', 'db_index': 'True'}),
            'Latitude': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'Longitude': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'Meta': {'object_name': 'PredefinedCity'},
            'city_encoded': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '200', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'isSMS': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'isSSS': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'null': 'True', 'to': u"orm['shoutit.User']"}),
            'video': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['shoutit.Video']", 'unique': 'True', 'null': 'True', 'on_delete': 'models.SET_NULL'})
        },
        'shoutit.report': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'IsDisabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'IsSolved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Report'},
            'Text': ('django.db.models.fields.TextField', [], {'default': "''", 'max_length': '300'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'object_id': ('uuidfield.fields.UUIDField', [], {'max_length': '32', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Reports'", 'to': u"orm['shoutit.User']"})
        },
        'shoutit.service': {
            'Code': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'Meta': {'object_name': 'Service'},
            'Name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'Price': ('django.db.models.fields.FloatField', [], {}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.servicebuy': {
            'Amount': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'DateBought': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'ServiceBuy'},
            'Service': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Buyers'", 'to': "orm['shoutit.Service']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Services'", 'to': u"orm['shoutit.User']"})
        },
        'shoutit.serviceusage': {
            'Amount': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'DateUsed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'ServiceUsage'},
            'Service': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'BuyersUsages'", 'to': "orm['shoutit.Service']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'ServicesUsages'", 'to': u"orm['shoutit.User']"})
        },
        'shoutit.sharedexperience': {
            'DateCreated': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'Experience': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'SharedExperiences'", 'to': "orm['shoutit.Experience']"}),
            'Meta': {'unique_together': "(('Experience', 'OwnerUser'),)", 'object_name': 'SharedExperience'},
            'OwnerUser': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'SharedExperiences'", 'to': u"orm['shoutit.User']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.storedfile': {
            'File': ('django.db.models.fields.URLField', [], {'max_length': '1024'}),
            'Meta': {'object_name': 'StoredFile'},
            'Type': ('django.db.models.fields.IntegerField', [], {}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Documents'", 'null': 'True', 'to': u"orm['shoutit.User']"})
        },
        'shoutit.storedimage': {
            'Image': ('django.db.models.fields.URLField', [], {'max_length': '1024'}),
            'Item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Images'", 'null': 'True', 'to': "orm['shoutit.Item']"}),
            'Meta': {'object_name': 'StoredImage'},
            'Shout': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'Images'", 'null': 'True', 'to': "orm['shoutit.Shout']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.stream': {
            'Meta': {'object_name': 'Stream'},
            'Type': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        'shoutit.stream2': {
            'Meta': {'unique_together': "(('content_type', 'object_id', 'type'),)", 'object_name': 'Stream2'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'listeners': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'listening'", 'symmetrical': 'False', 'through': "orm['shoutit.Listen']", 'to': u"orm['shoutit.User']"}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'shoutit.user': {
            'Meta': {'object_name': 'User'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
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
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'shoutit.userpermission': {
            'Meta': {'object_name': 'UserPermission'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'date_given': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'permission': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoutit.Permission']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shoutit.User']"})
        },
        'shoutit.video': {
            'Meta': {'object_name': 'Video'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'duration': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'id_on_provider': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'videos'", 'null': 'True', 'to': "orm['shoutit.Item']"}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('uuidfield.fields.UUIDField', [], {'unique': 'True', 'max_length': '32', 'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['shoutit']