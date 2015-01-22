from django.db import models
from apps.shoutit.models.base import UUIDModel, User
from settings import AUTH_USER_MODEL


class DBCLUser(UUIDModel):
    class Meta(UUIDModel.Meta):
        abstract = True

    user = models.OneToOneField(AUTH_USER_MODEL, related_name='%(class)s', unique=True, db_index=True)


class CLUser(DBCLUser):
    cl_email = models.EmailField(max_length=254)


@property
def cl_user(self):
    if hasattr(self, '_cl_user') and self._cl_user:
        return self._cl_user
    try:
        self._cl_user = self.cluser
    except CLUser.DoesNotExist:
        self._cl_user = None

    return self._cl_user
User.add_to_class('cl_user', cl_user)

@property
def cl_ad_id(self):
    if hasattr(self, '_cl_ad_id') and self._cl_ad_id:
        return self._cl_ad_id
    try:
        self._cl_ad_id = self.email.split('@')[0].split('-')[1]
    except CLUser.DoesNotExist:
        self._cl_ad_id = None

    return self._cl_ad_id
User.add_to_class('cl_ad_id', cl_ad_id)


class DBCLConversation(UUIDModel):
    in_email = models.EmailField(max_length=254, null=True)
    from_user = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    to_user = models.ForeignKey(AUTH_USER_MODEL, related_name='+')
    shout = models.ForeignKey('Trade')
    ref = models.CharField(max_length=100, null=True)