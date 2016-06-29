from __future__ import unicode_literals

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

from shoutit.controllers import (email_controller, item_controller, location_controller, mixpanel_controller, notifications_controller)
from shoutit.models import Shout
from shoutit.models.misc import delete_object_index
from shoutit.models.post import ShoutIndex, ShoutLike
from shoutit.utils import debug_logger, error_logger


def delete_post(post):
    post.is_disabled = True
    post.save()


# Todo: make api for renewing shouts
def RenewShout(request, shout_id, days=int(settings.MAX_EXPIRY_DAYS)):
    shout = Shout.objects.get(pk=shout_id)
    if not shout:
        raise ObjectDoesNotExist()
    else:
        now = timezone.now()
        shout.published_at = now
        shout.expires_at = now + timedelta(days=days)
        shout.renewal_count += 1
        shout.expiry_notified = False
        shout.save()


# Todo: implement better method
def NotifyPreExpiry():
    shouts = Shout.objects.all()
    for shout in shouts:
        if not shout.expiry_notified:
            expires_at = shout.expires_at
            if not expires_at:
                expires_at = shout.published_at + timedelta(days=settings.MAX_EXPIRY_DAYS)
            if (expires_at - timezone.now()).days < settings.SHOUT_EXPIRY_NOTIFY:
                if shout.user.email:
                    email_controller.SendExpiryNotificationEmail(shout.user, shout)
                    shout.expiry_notified = True
                    shout.save()


def create_shout_v2(user, shout_type, title, text, price, currency, category, tags, location, filters=None, images=None,
                    videos=None, published_at=None, exp_days=None, priority=0, page_admin_user=None,
                    publish_to_facebook=None, api_client=None, api_version=None):
    # tags
    # if passed as [{'name': 'tag-x'},...]
    if tags:
        if not isinstance(tags[0], basestring):
            tags = map(lambda t: t.get('name'), tags)
    # filters
    if not filters:
        filters = {}
    # item
    item = item_controller.create_item(name=title, description=text, price=price, currency=currency, images=images,
                                       videos=videos)
    shout = Shout(user=user, type=shout_type, text=text, category=category, tags=tags, filters=filters, item=item,
                  priority=priority, page_admin_user=page_admin_user)
    location_controller.update_object_location(shout, location, save=False)

    # Published and Expires
    if published_at:
        shout.published_at = published_at
    if exp_days:
        shout.expires_at = published_at + timedelta(days=exp_days)

    shout.api_client, shout.api_version = api_client, api_version
    shout.publish_to_facebook = publish_to_facebook
    shout.save()

    location_controller.add_predefined_city(location)
    return shout


def create_shout(user, shout_type, title, text, price, currency, category, location, filters=None, images=None,
                 videos=None, published_at=None, is_sss=False, exp_days=None, priority=0, page_admin_user=None,
                 publish_to_facebook=None, available_count=None, is_sold=None, mobile=None, api_client=None,
                 api_version=None):
    # Filters
    if not filters:
        filters = {}

    # Create the Item
    item = item_controller.create_item(name=title, description=text, price=price, currency=currency, images=images,
                                       videos=videos, available_count=available_count, is_sold=is_sold)
    # Prepare the Shout
    shout = Shout(user=user, type=shout_type, text=text, category=category, item=item, filters=filters,
                  mobile=mobile, is_sss=is_sss, priority=priority, page_admin_user=page_admin_user)
    location_controller.update_object_location(shout, location, save=False)

    # Published and Expires
    if published_at:
        shout.published_at = published_at
    if exp_days:
        shout.expires_at = published_at + timedelta(days=exp_days)

    # Set attributes for post saving and tracking
    shout.api_client, shout.api_version = api_client, api_version
    shout.publish_to_facebook = publish_to_facebook

    # Save
    try:
        shout.save()
    except (ValidationError, IntegrityError):
        item.delete()
        raise
    location_controller.add_predefined_city(location)
    return shout


def edit_shout(shout, title=None, text=None, price=None, currency=None, category=None, filters=None, images=None,
               videos=None, location=None, page_admin_user=None, available_count=None, is_sold=None, mobile=None,
               publish_to_facebook=None):
    item_controller.edit_item(shout.item, name=title, description=text, price=price, currency=currency, images=images,
                              videos=videos, available_count=available_count, is_sold=is_sold)
    # Can be unset
    shout.text = text
    shout.mobile = mobile

    # Can't be unset
    if category is not None:
        shout.category = category

    if filters is not None:
        shout.filters = filters

    if location is not None:
        location_controller.update_object_location(shout, location, save=False)
        location_controller.add_predefined_city(location)

    if page_admin_user is not None:
        shout.page_admin_user = page_admin_user

    shout.publish_to_facebook = publish_to_facebook
    shout.save()
    return shout


def edit_shout_v2(shout, shout_type=None, title=None, text=None, price=None, currency=None, category=None, tags=None,
                  filters=None, images=None, videos=None, location=None, page_admin_user=None):
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
        shout.tags = tags
    if filters:
        shout.filters = filters
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
        # Track
        if not instance.is_sss:
            mixpanel_controller.track(instance.user.pk, 'new_shout', instance.track_properties)

    # Publish to Facebook
    if getattr(instance, 'publish_to_facebook', False) and 'facebook' not in instance.published_on:
        publish_shout_to_facebook.delay(instance)


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
    # Update the shout object without dispatching signals
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
    for k, v in shout.filters.items():
        shout_index.filters[k] = v
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
    shout_index.is_muted = shout.is_muted
    shout_index.uid = shout.user.pk
    shout_index.username = shout.user.username
    shout_index.published_at = shout.published_at
    shout_index.expires_at = shout.expires_at
    shout_index.currency = shout.item.currency.code if shout.item.currency else None
    shout_index.address = shout.address
    shout_index.thumbnail = shout.thumbnail
    shout_index.video_url = shout.video_url
    shout_index.is_sss = shout.is_sss
    shout_index.priority = shout.priority
    return shout_index


@job(settings.RQ_QUEUE)
def publish_shout_to_facebook(shout):
    la = getattr(shout.user, 'linked_facebook', None)
    if not la:
        debug_logger.debug('No linked_facebook, skip publishing Shout %s on Facebook' % shout)
        return
    if 'publish_actions' not in la.scopes:
        debug_logger.debug('No publish_actions in scopes, skip publishing Shout %s on Facebook' % shout)
        return
    prod = settings.SHOUTIT_ENV == 'prod'
    namespace = 'shoutitcom' if prod else 'shoutitcom-' + settings.SHOUTIT_ENV
    actions_url = 'https://graph.facebook.com/me/%s:shout' % namespace
    params = {
        'access_token': la.access_token,
        shout.get_type_display(): shout.web_url,
        'fb:explicitly_shared': prod,
        'privacy': "{'value':'EVERYONE'}"
    }
    res = requests.post(actions_url, params=params).json()
    id_on_facebook = res.get('id')
    if id_on_facebook:
        shout.published_on['facebook'] = id_on_facebook
        shout.save(update_fields=['published_on'])
        debug_logger.debug('Published shout %s on Facebook' % shout)
    else:
        error_logger.warn('Error publishing shout on Facebook', extra={'res': res, 'shout': shout})


def like_shout(user, shout, api_client=None, api_version=None, page_admin_user=None):
    shout_like = ShoutLike.create(save=False, user=user, shout=shout, page_admin_user=page_admin_user)
    shout_like.api_client, shout_like.api_version = api_client, api_version
    try:
        shout_like.save()
        notifications_controller.notify_shout_owner_of_shout_like(shout, user)
    except (ValidationError, IntegrityError):
        pass


def unlike_shout(user, shout):
    ShoutLike.objects.filter(user=user, shout=shout).delete()


@receiver(post_save, sender=ShoutLike)
def shout_like_post_save(sender, instance=None, created=False, **kwargs):
    if created:
        # Track
        mixpanel_controller.track(instance.user.pk, 'new_shout_like', instance.track_properties)
