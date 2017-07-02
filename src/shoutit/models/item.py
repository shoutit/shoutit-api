from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import ugettext_lazy as _

from common.constants import ITEM_STATE_AVAILABLE
from shoutit.models.base import UUIDModel
from shoutit.utils import none_to_blank


class Item(UUIDModel):
    name = models.CharField(max_length=500, blank=True, default='')
    description = models.TextField(max_length=10000, blank=True, default='')
    price = models.BigIntegerField(null=True, blank=True)
    price_usd = models.BigIntegerField(null=True, blank=True)
    currency = models.ForeignKey('shoutit.Currency', null=True, blank=True, on_delete=models.PROTECT)
    state = models.IntegerField(default=ITEM_STATE_AVAILABLE.value, db_index=True)
    available_count = models.PositiveSmallIntegerField(default=1)
    is_sold = models.BooleanField(default=False, db_index=True)
    images = ArrayField(models.URLField(), default=list, blank=True)
    videos = models.ManyToManyField('shoutit.Video', blank=True, related_name='items')

    def __str__(self):
        return "%s" % (self.name[:30] or '[Item]')

    def clean(self):
        none_to_blank(self, ['name', 'description'])
        has_price = self.price is not None and self.currency is not None
        self.price_usd = int(self.price * self.currency.usd) if has_price else 0

    @property
    def thumbnail(self):
        if self.images:
            return self.images[0]
        elif self.videos.all():
            return self.videos.all()[0].thumbnail_url
        else:
            return None

    @property
    def video_url(self):
        return self.videos.all()[0].url if self.videos.all() else None

    @property
    def currency_code(self):
        return self.currency.code if self.currency else None

    @property
    def v2_price(self):
        return round(float(self.price / 100.0), 2) if self.price is not None else 0


class Currency(UUIDModel):
    code = models.CharField(max_length=10)
    country = models.CharField(max_length=10, blank=True)
    name = models.CharField(max_length=64, null=True, blank=True)
    usd = models.FloatField(default=1, help_text=_('Equivalent to 1 USD'))

    def __str__(self):
        return '[' + self.code + '] '
