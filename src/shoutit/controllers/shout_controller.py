from __future__ import unicode_literals

from collections import OrderedDict
from datetime import datetime, timedelta
import random

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.conf import settings
from django_rq import job
from django.db.models.signals import post_save
from django.dispatch import receiver
from elasticsearch import NotFoundError

from common.utils import process_tags
from shoutit.models.misc import delete_object_index
from shoutit.models.post import ShoutIndex
from common.constants import (POST_TYPE_OFFER, POST_TYPE_REQUEST, POST_TYPE_EXPERIENCE)
from shoutit.models import Shout, Post
from shoutit.controllers import email_controller, item_controller, location_controller, tag_controller
from shoutit.utils import debug_logger, track


def get_post(post_id, find_muted=False, find_expired=False):
    post = Post.objects.filter(id=post_id, is_disabled=False).select_related('user', 'user__business', 'user__profile')
    if not find_muted:
        post = post.filter(muted=False)

    if not find_expired:
        today = datetime.today()
        days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
        begin = today - days
        post = post.filter(
            (~Q(type=POST_TYPE_REQUEST) & ~Q(type=POST_TYPE_OFFER))
            |
            ((Q(shout__expiry_date__isnull=True, date_published__range=(begin, today))

              | Q(shout__expiry_date__isnull=False, date_published__lte=F('shout__expiry_date')))
             & (Q(type=POST_TYPE_REQUEST) | Q(type=POST_TYPE_OFFER)))
        ).select_related()
    if post:
        post = post[0]
        if post.type == POST_TYPE_OFFER or post.type == POST_TYPE_REQUEST:
            return post.shout
        elif post.type == POST_TYPE_EXPERIENCE:
            return post.experience
    else:
        return None


def delete_post(post):
    post.is_disabled = True
    post.save()


# todo: make api for renewing shouts
def RenewShout(request, shout_id, days=int(settings.MAX_EXPIRY_DAYS)):
    shout = Shout.objects.get(pk=shout_id)
    if not shout:
        raise ObjectDoesNotExist()
    else:
        now = datetime.now()
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
            if (expiry_date - datetime.now()).days < settings.SHOUT_EXPIRY_NOTIFY:
                if shout.user.email:
                    email_controller.SendExpiryNotificationEmail(shout.user, shout)
                    shout.expiry_notified = True
                    shout.save()


# todo: handle exception on each step and in case of errors, rollback!
def create_shout(user, shout_type, title, text, price, currency, category, tags, location, tags2=None, images=None,
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
    tags.insert(0, category.main_tag.name)
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
        date_published = datetime.today()
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


def edit_shout(shout, shout_type=None, title=None, text=None, price=None, currency=None, category=None, tags=None,
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
        if not category:
            category = shout.category
        tags.insert(0, category.main_tag.name)
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
    action = 'Created' if created else 'Updated'
    log = '%s Shout: %s: %s, %s: %s' % (action, instance.pk, instance.item.name, instance.country, instance.city)
    debug_logger.debug(log)
    # Create / Update ShoutIndex
    save_shout_index(instance, created)
    if created:
        # Publish to Facebook
        if getattr(instance, 'publish_to_facebook', False):
            publish_to_facebook(instance)
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
        if shout.is_disabled:
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
    shout_index.category = shout.category.name
    shout_index.country = shout.country
    shout_index.postal_code = shout.postal_code
    shout_index.state = shout.state
    shout_index.city = shout.city
    shout_index.latitude = shout.latitude
    shout_index.longitude = shout.longitude
    shout_index.price = shout.item.price if shout.item.price is not None else 0
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
def publish_to_facebook(shout):
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
