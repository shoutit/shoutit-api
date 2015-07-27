from __future__ import unicode_literals

from collections import OrderedDict
from datetime import datetime, timedelta
import random
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.conf import settings
from django_rq import job
from django.db.models.signals import post_save
from django.dispatch import receiver
from elasticsearch import NotFoundError, ConflictError
from common.utils import process_tags
from shoutit.controllers.user_controller import update_object_location, add_predefined_city
from shoutit.models.post import ShoutIndex
from common.constants import (POST_TYPE_OFFER, POST_TYPE_REQUEST, POST_TYPE_EXPERIENCE)
from common.constants import EVENT_TYPE_SHOUT_OFFER, EVENT_TYPE_SHOUT_REQUEST
from shoutit.models import Shout, Post
from shoutit.controllers import event_controller, email_controller, item_controller
from shoutit.utils import debug_logger, track


def get_post(post_id, find_muted=False, find_expired=False):
    post = Post.objects.filter(id=post_id, is_disabled=False).select_related('user',
                                                                             'user__business',
                                                                             'user__profile')
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
    event_controller.delete_event_about_obj(post)


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
def create_shout(user, shout_type, title, text, price, currency, category, tags, location,
                 images=None, videos=None, date_published=None, is_sss=False, exp_days=None, priority=0):
    # tags
    # if passed as [{'name': 'tag-x'},...]
    if tags:
        if not isinstance(tags[0], basestring):
            tags = [tag.get('name') for tag in tags]
    # remove duplicates
    tags = list(OrderedDict.fromkeys(tags))
    # process tags
    tags = process_tags(tags)
    # add main_tag from category
    tags.insert(0, category.main_tag.name)
    # item
    item = item_controller.create_item(name=title, description=text, price=price, currency=currency, images=images, videos=videos)

    shout = Shout()
    shout.type = shout_type
    shout.text = text
    shout.user = user
    shout.category = category
    shout.tags = tags
    shout.item = item
    shout.is_sss = is_sss
    shout.priority = priority
    update_object_location(shout, location, save=False)

    if not date_published:
        date_published = datetime.today()
        if is_sss:
            hours = random.randrange(-5, 0)
            minutes = random.randrange(-59, 0)
            date_published += timedelta(hours=hours, minutes=minutes)
    shout.date_published = date_published
    shout.expiry_date = exp_days and (date_published + timedelta(days=exp_days)) or None

    shout.save()
    user.profile.stream.add_post(shout)

    add_tags_to_shout(tags, shout)
    add_predefined_city(location)

    event_type = EVENT_TYPE_SHOUT_OFFER if shout_type == POST_TYPE_OFFER else EVENT_TYPE_SHOUT_REQUEST
    event_controller.register_event(user, event_type, shout)
    return shout


def edit_shout(shout, title=None, text=None, price=None, currency=None, category=None, tags=None,
               images=None, videos=None, location=None):
    item_controller.edit_item(shout.item, name=title, description=text, price=price, currency=currency, images=images, videos=videos)
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
        add_tags_to_shout(tags, shout)
    if location:
        update_object_location(shout, location, save=False)
        add_predefined_city(location)
    shout.save()
    return shout


def add_tags_to_shout(tags, shout):
    from shoutit.controllers import tag_controller
    # todo: optimize
    # remove old tags first if they exist
    for tag in shout.tag_objects:
        tag.stream.remove_post(shout)
    # add new ones
    for tag in tag_controller.get_or_create_tags(tags, shout.user):
        # prevent adding existing tags
        try:
            tag.stream.add_post(shout)
        except IntegrityError:
            pass


@receiver(post_save, sender=Shout)
def shout_post_save(sender, instance=None, created=False, **kwargs):
    action = 'Created' if created else 'Updated'
    debug_logger.debug('{} Shout: {}: {}, {}: {}'.format(action, instance.pk, instance.item.name,
                                                         instance.country, instance.city))
    # save index
    save_shout_index(instance, created)
    # track
    if created and not instance.is_sss:
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
            return delete_shout_index(shout)
        shout_index = ShoutIndex.get(shout.pk)
    except NotFoundError:
        shout_index = ShoutIndex()
        shout_index._id = shout.pk
    shout_index.type = shout.type_name
    shout_index.title = shout.item.name
    shout_index.text = shout.text
    shout_index.tags = shout.tags
    shout_index.tags_count = len(shout.tags)
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
    if shout_index.save():
        debug_logger.debug('Created ShoutIndex: %s' % shout.pk)
    else:
        debug_logger.debug('Updated ShoutIndex: %s' % shout.pk)


def delete_shout_index(shout):
    try:
        shout_index = ShoutIndex.get(shout.pk)
        shout_index.delete()
        debug_logger.debug('Deleted ShoutIndex: %s' % shout.pk)
    except NotFoundError:
        debug_logger.debug('ShoutIndex: %s not found' % shout.pk)
    except ConflictError:
        debug_logger.debug('ShoutIndex: %s already deleted' % shout.pk)

