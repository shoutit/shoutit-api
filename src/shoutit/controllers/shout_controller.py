from __future__ import unicode_literals

import random
from collections import OrderedDict
from datetime import timedelta

import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django_rq import job
from elasticsearch import NotFoundError

from common.utils import process_tags
from shoutit.controllers import email_controller, item_controller, location_controller, tag_controller
from shoutit.models import Shout
from shoutit.models.misc import delete_object_index
from shoutit.models.post import ShoutIndex
from shoutit.utils import debug_logger, track


def delete_post(post):
    post.is_disabled = True
    post.save()


# todo: make api for renewing shouts
def RenewShout(request, shout_id, days=int(settings.MAX_EXPIRY_DAYS)):
    shout = Shout.objects.get(pk=shout_id)
    if not shout:
        raise ObjectDoesNotExist()
    else:
        now = timezone.now()
        shout.date_published = now
        shout.expiry_date = now + timedelta(days=days)
        shout.renewal_count += 1
        shout.expiry_notified = False
        shout.save()


# todo: implement better method
def NotifyPreExpiry():
    shouts = Shout.objects.all()
    for shout in shouts:
        if not shout.expiry_notified:
            expiry_date = shout.expiry_date
            if not expiry_date:
                expiry_date = shout.date_published + timedelta(days=settings.MAX_EXPIRY_DAYS)
            if (expiry_date - timezone.now()).days < settings.SHOUT_EXPIRY_NOTIFY:
                if shout.user.email:
                    email_controller.SendExpiryNotificationEmail(shout.user, shout)
                    shout.expiry_notified = True
                    shout.save()


def create_shout_v2(user, shout_type, title, text, price, currency, category, tags, location, tags2=None, images=None,
                    videos=None, date_published=None, is_sss=False, exp_days=None, priority=0, page_admin_user=None,
                    publish_to_facebook=None):
    # tags
    # if passed as [{'name': 'tag-x'},...]
    if tags:
        if not isinstance(tags[0], basestring):
            tags = map(lambda t: t.get('name'), tags)
    # process tags
    tags = process_tags(tags)
    # add main_tag from category
    tags.insert(0, category.slug)
    # remove duplicates
    tags = list(OrderedDict.fromkeys(tags))
    # Create actual tags objects (when necessary)
    tag_controller.get_or_create_tags(tags, user)
    # tags2
    if not tags2:
        tags2 = {}
    for k, v in tags2.items():
        tags2[k] = str(v)
    # item
    item = item_controller.create_item(name=title, description=text, price=price, currency=currency, images=images,
                                       videos=videos)
    shout = Shout.create(user=user, type=shout_type, text=text, category=category, tags=tags, tags2=tags2, item=item,
                         is_sss=is_sss, priority=priority, save=False, page_admin_user=page_admin_user)
    location_controller.update_object_location(shout, location, save=False)

    if not date_published:
        date_published = timezone.now()
        if is_sss:
            hours = random.randrange(-5, 0)
            minutes = random.randrange(-59, 0)
            date_published += timedelta(hours=hours, minutes=minutes)
    shout.date_published = date_published
    shout.expiry_date = exp_days and (date_published + timedelta(days=exp_days)) or None
    shout.publish_to_facebook = publish_to_facebook
    shout.save()

    location_controller.add_predefined_city(location)
    return shout


def create_shout(user, shout_type, title, text, price, currency, category, location, filters=None, images=None,
                 videos=None, date_published=None, is_sss=False, exp_days=None, priority=0, page_admin_user=None,
                 publish_to_facebook=None, available_count=None, is_sold=None, mobile=None):
    # tags2
    tags2 = {}
    if not filters:
        filters = []
    for f in filters:
        tags2[f['slug']] = str(f['value']['slug'])
    # tags
    tags = tags2.values()
    tags = list(OrderedDict.fromkeys(tags))
    tags.insert(0, category.slug)
    # Create actual tags objects (when necessary)
    tag_controller.get_or_create_tags(tags, user)
    # item
    item = item_controller.create_item(name=title, description=text, price=price, currency=currency, images=images,
                                       videos=videos, available_count=available_count, is_sold=is_sold)
    shout = Shout.create(user=user, type=shout_type, text=text, category=category, tags=tags, tags2=tags2, item=item,
                         is_sss=is_sss, priority=priority, save=False, page_admin_user=page_admin_user, mobile=mobile)
    location_controller.update_object_location(shout, location, save=False)

    if not date_published:
        date_published = timezone.now()
        if is_sss:
            hours = random.randrange(-5, 0)
            minutes = random.randrange(-59, 0)
            date_published += timedelta(hours=hours, minutes=minutes)
    shout.date_published = date_published
    shout.expiry_date = exp_days and (date_published + timedelta(days=exp_days)) or None
    shout.publish_to_facebook = publish_to_facebook
    try:
        shout.save()
    except (ValidationError, IntegrityError):
        item.delete()
        raise
    location_controller.add_predefined_city(location)
    return shout


def edit_shout(shout, title=None, text=None, price=None, currency=None, category=None, filters=None, images=None,
               videos=None, location=None, page_admin_user=None, available_count=None, is_sold=None, mobile=None):
    item_controller.edit_item(shout.item, name=title, description=text, price=price, currency=currency, images=images,
                              videos=videos, available_count=available_count, is_sold=is_sold)
    # Can be unset
    shout.text = text
    shout.mobile = mobile

    # Can't be unset
    if category is not None:
        shout.category = category
    if filters is not None:
        tags2 = {}
        for f in filters:
            tags2[f['slug']] = str(f['value']['slug'])
        shout.tags2 = tags2

        tags = tags2.values()
        tags = list(OrderedDict.fromkeys(tags))
        tags.insert(0, shout.category.slug)
        shout.tags = tags
        # Create actual tags objects (when necessary)
        tag_controller.get_or_create_tags(tags, shout.user)
    if location is not None:
        location_controller.update_object_location(shout, location, save=False)
        location_controller.add_predefined_city(location)
    if page_admin_user is not None:
        shout.page_admin_user = page_admin_user

    shout.save()
    return shout


def edit_shout_v2(shout, shout_type=None, title=None, text=None, price=None, currency=None, category=None, tags=None,
                  tags2=None, images=None, videos=None, location=None, page_admin_user=None):
    item_controller.edit_item(shout.item, name=title, description=text, price=price, currency=currency, images=images,
                              videos=videos)
    if shout_type:
        shout.type = shout_type
    if text:
        shout.text = text
    if category:
        shout.category = category
    if tags:
        # if passed as [{'name': 'tag-x'},...]
        if not isinstance(tags[0], basestring):
            tags = [tag.get('name') for tag in tags]
        # remove duplicates
        tags = list(OrderedDict.fromkeys(tags))
        # process tags
        tags = process_tags(tags)
        # add main_tag from category
        tags.insert(0, shout.category.slug)
        shout.tags = tags
        # Create actual tags objects (when necessary)
        tag_controller.get_or_create_tags(tags, shout.user)
    if tags2:
        shout.tags2 = tags2
    if location:
        location_controller.update_object_location(shout, location, save=False)
        location_controller.add_predefined_city(location)
    if page_admin_user:
        shout.page_admin_user = page_admin_user
    shout.save()
    return shout


@receiver(post_save, sender=Shout)
def shout_post_save(sender, instance=None, created=False, **kwargs):
    # Create / Update ShoutIndex
    save_shout_index(instance, created)
    if created:
        # Publish to Facebook
        if getattr(instance, 'publish_to_facebook', False):
            publish_shout_to_facebook.delay(instance)
        # track
        if not instance.is_sss:
            track(instance.user.pk, 'new_shout', instance.track_properties)


def save_shout_index(shout=None, created=False, delay=True):
    if delay:
        shout = Shout.objects.get(id=shout.id)
        return _save_shout_index.delay(shout, created)
    return _save_shout_index(shout, created)


@job(settings.RQ_QUEUE)
def _save_shout_index(shout=None, created=False):
    try:
        if created:
            raise NotFoundError()
        if shout.is_disabled or shout.muted:
            return delete_object_index(ShoutIndex, shout)
        shout_index = ShoutIndex.get(shout.pk)
    except NotFoundError:
        shout_index = ShoutIndex()
        shout_index._id = shout.pk
    shout_index = shout_index_from_shout(shout, shout_index)
    if shout_index.save():
        debug_logger.debug('Created ShoutIndex: %s' % shout.pk)
    else:
        debug_logger.debug('Updated ShoutIndex: %s' % shout.pk)
    # Update the location object without dispatching signals
    shout._meta.model.objects.filter(id=shout.id).update(is_indexed=True)


def shout_index_from_shout(shout, shout_index=None):
    if shout_index is None:
        shout_index = ShoutIndex()
        shout_index._id = shout.pk
    shout_index.type = shout.get_type_display()
    shout_index.title = shout.item.name
    shout_index.text = shout.text
    shout_index.tags = shout.tags
    shout_index.tags_count = len(shout.tags)
    for k, v in shout.tags2.items():
        shout_index.tags2[k] = v
    shout_index.category = shout.category.slug
    shout_index.country = shout.country
    shout_index.postal_code = shout.postal_code
    shout_index.state = shout.state
    shout_index.city = shout.city
    shout_index.latitude = shout.latitude
    shout_index.longitude = shout.longitude
    shout_index.price = shout.item.price if shout.item.price is not None else 0
    shout_index.available_count = shout.available_count
    shout_index.is_sold = shout.is_sold
    shout_index.uid = shout.user.pk
    shout_index.username = shout.user.username
    shout_index.date_published = shout.date_published
    shout_index.currency = shout.item.currency.code if shout.item.currency else None
    shout_index.address = shout.address
    shout_index.thumbnail = shout.thumbnail
    shout_index.video_url = shout.video_url
    shout_index.is_sss = shout.is_sss
    shout_index.priority = shout.priority
    return shout_index


@job(settings.RQ_QUEUE)
def publish_shout_to_facebook(shout):
    la = shout.user.linked_facebook
    if not la or 'publish_actions' not in la.scopes:
        return
    actions_url = 'https://graph.facebook.com/me/shoutitcom:shout'
    params = {
        'access_token': la.access_token,
        'method': 'POST',
        shout.get_type_display(): shout.web_url
    }
    res = requests.post(actions_url, params=params).json()
    id_on_facebook = res.get('id')
    if id_on_facebook:
        shout.published_on['facebook'] = id_on_facebook
        shout.save(update_fields=['published_on'])
