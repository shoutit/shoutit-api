from django.conf import settings
from django.db import models
from shoutit.models import Shout
from shoutit.models.base import UUIDModel


class DBCLUser(UUIDModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='%(class)s')
    converted_at = models.DateTimeField(verbose_name="Conversion time", null=True, blank=True)

    class Meta(UUIDModel.Meta):
        abstract = True

    def __str__(self):
        return "%s:%s" % (self.pk, self.user)

    @property
    def shout(self):
        return Shout.objects.filter(user=self.user).first()


class CLUser(DBCLUser):
    cl_email = models.EmailField(max_length=254)


class DBUser(DBCLUser):
    db_link = models.URLField(max_length=1000)


class DBZ2User(DBCLUser):
    db_link = models.URLField(max_length=1000)


class DBCLConversation(UUIDModel):
    in_email = models.EmailField(max_length=254, null=True, blank=True)
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='+')
    shout = models.ForeignKey('shoutit.Shout')
    ref = models.CharField(max_length=100, null=True, blank=True)
    sms_code = models.CharField(max_length=10, default='', blank=True)

    def clean(self):
        if isinstance(self.sms_code, str):
            if self._state.adding:
                self.sms_code = 'Z' + self.sms_code
            self.sms_code = self.sms_code.upper()
