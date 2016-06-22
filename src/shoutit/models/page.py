from __future__ import unicode_literals

from django.conf import settings
from django.core import validators
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from common.constants import (PageAdminType, PAGE_ADMIN_TYPE_EDITOR, USER_TYPE_PAGE, PAGE_ADMIN_TYPE_OWNER,
                              PAGE_ADMIN_TYPE_ADMIN)
from shoutit.models.base import UUIDModel
from shoutit.models.auth import AbstractProfile
from shoutit.models.tag import ShoutitSlugField
from shoutit.utils import correct_mobile

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')


class PageCategory(MPTTModel, UUIDModel):
    name = models.CharField(max_length=100, db_index=True)
    slug = ShoutitSlugField(unique=True)
    image = models.URLField(blank=True, default='')
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['slug']

    def __unicode__(self):
        return unicode(self.name)


class Page(AbstractProfile):
    creator = models.ForeignKey(AUTH_USER_MODEL, related_name='pages_created')
    admins = models.ManyToManyField(AUTH_USER_MODEL, blank=True, through='shoutit.PageAdmin', related_name='pages')
    name = models.CharField(_('name'), max_length=75, validators=[validators.MinLengthValidator(2)])
    category = models.ForeignKey('shoutit.PageCategory', related_name='pages', on_delete=models.PROTECT)

    is_published = models.BooleanField(_('published'), default=False,
                                       help_text=_('Designates whether the page is publicly visible.'))
    is_claimed = models.BooleanField(_('claimed'), default=False,
                                     help_text=_('Designates whether the page is claimed.'))

    about = models.TextField(_('about'), max_length=150, blank=True, default='')
    description = models.TextField(_('description'), max_length=1000, blank=True, default='')
    phone = models.CharField(_('phone'), max_length=30, blank=True, default='')
    founded = models.TextField(_('founded'), max_length=50, blank=True, default='')
    impressum = models.TextField(_('impressum'), max_length=2000, blank=True, default='')
    overview = models.TextField(_('overview'), max_length=1000, blank=True, default='')
    mission = models.TextField(_('mission'), max_length=1000, blank=True, default='')
    general_info = models.TextField(_('general info'), max_length=1000, blank=True, default='')
    # hours = JSONField...

    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return unicode(self.user)

    def update(self, name=None):
        # Todo (mo): UUIDModel already has update method, use it maybe?
        update_fields = []
        if name is not None:
            self.name = name
            update_fields.append('name')
        self.save(update_fields=update_fields)

    def clean(self):
        super(Page, self).clean()
        self.phone = correct_mobile(self.phone, self.country)

    def is_admin(self, user):
        return user in self.admins.all()

    def add_admin(self, user, admin_type=PAGE_ADMIN_TYPE_ADMIN):
        PageAdmin.create(page=self, admin=user, type=admin_type)

    def remove_admin(self, user):
        PageAdmin.objects.filter(page=self, admin=user).delete()


class PageAdmin(UUIDModel):
    page = models.ForeignKey('shoutit.Page')
    admin = models.ForeignKey(AUTH_USER_MODEL)
    type = models.PositiveSmallIntegerField(choices=PageAdminType.choices, default=PAGE_ADMIN_TYPE_EDITOR.value)


@receiver(post_save, sender='shoutit.Page')
def page_post_save(sender, instance=None, created=False, **kwargs):
    if created:
        PageAdmin.create(page=instance, admin=instance.creator, type=PAGE_ADMIN_TYPE_OWNER)


@receiver(post_save, sender=AUTH_USER_MODEL)
def user_post_save(sender, instance=None, created=False, update_fields=None, **kwargs):
    """

    """
    if instance.type != USER_TYPE_PAGE:
        return

    if created:
        # Create page
        page_fields = getattr(instance, 'page_fields', {})
        Page.create(id=instance.id, user=instance, **page_fields)

        # Todo: give appropriate permissions
