from django.db import models

from shoutit.models.misc import UUIDModel
from common import constants


class Request(UUIDModel):
    ip_address = models.IPAddressField(default='0.0.0.0', db_index=True)
    user = models.ForeignKey('shoutit.User', null=True, related_name='requests', db_index=True)
    session_id = models.TextField(default='', db_index=True)
    url = models.URLField(default='', max_length=8192, blank=True)
    plain_url = models.URLField(default='', blank=True, db_index=True, max_length=8192)
    method = models.CharField(max_length=20, db_index=True)
    is_ajax = models.BooleanField(default=False)
    is_api = models.BooleanField(default=False)
    user_agent = models.TextField(default='', blank=True)
    referer = models.URLField(max_length=8192, default='', blank=True)
    date_visited = models.DateTimeField(auto_now_add=True)
    token = models.ForeignKey('piston3.Token', null=True, related_name='+')

    def __unicode__(self):
        return '%s %s from %s @ %s by %s' % (self.method, self.plain_url, self.ip_address, self.date_visited.strftime('%Y/%m/%d %H:%M:%S'), 'anonymous' if self.user is None else self.user.username)


class DataDict(object):
    activity = None

    def __init__(self, activity=None):
        self.activity = activity

    def __getitem__(self, item):
        for kv in self.activity.data.all():
            if kv.key == item:
                return kv.value
        raise KeyError('Key %s was not found.' % item)

    def __setitem__(self, key, value):
        for kv in self.activity.data.all():
            if kv.key == key:
                kv.value = value
                return
        kv = ActivityData(key=key, value=value, activity=self.activity)
        self.activity.data.add(kv)


class Activity(UUIDModel):
    type = models.IntegerField(default=0, db_index=True)
    request = models.ForeignKey(Request, related_name='activities', db_index=True)
    __dict = None

    def __init__(self, *args, **kwargs):
        super(Activity, self).__init__(*args, **kwargs)
        self.__dict = DataDict(self)

    def add_data(self, data):
        for k, v in data.iteritems():
            kv = ActivityData(key=k, value=v, activity=self)
            self.data.add(kv)

    @property
    def data_dict(self):
        return self.__dict

    def __unicode__(self):
        return unicode(constants.ActivityType.values[self.type]) + ' : ' + unicode(self.request)


class ActivityData(UUIDModel):

    def __unicode__(self):
        return unicode(self.pk) + ": " + unicode(self.activity_id) + ": " + unicode(self.value)

    activity = models.ForeignKey(Activity, related_name='data', db_index=True)
    key = models.IntegerField(default=0, db_index=True)
    value = models.TextField()