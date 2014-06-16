from django.db import models
from django.contrib.auth.models import User


class LinkedGoogleAccount(models.Model):

    user = models.ForeignKey(User, related_name='linked_google')
    credentials_json = models.CharField(max_length=2048)
    gplus_id = models.CharField(max_length=64, db_index=True)

    #expires_in = models.BigIntegerField(default=0)
    #verified = models.BooleanField(default=False)

    class Meta:
        app_label = 'shoutit'
