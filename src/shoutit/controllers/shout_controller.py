from __future__ import unicode_literals

from collections import OrderedDict
from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.conf import settings
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from elasticsearch import NotFoundError, ConflictError
from shoutit.models.post import ShoutIndex
from common.constants import POST_TYPE_OFFER, POST_TYPE_REQUEST, POST_TYPE_EXPERIENCE, \
    DEFAULT_CURRENCY_CODE
from common.constants import EVENT_TYPE_SHOUT_OFFER, EVENT_TYPE_SHOUT_REQUEST
from shoutit.models import Shout, Post, PredefinedCity
from shoutit.controllers import event_controller, email_controller, item_controller
from shoutit.utils import to_seo_friendly

logger = logging.getLogger('shoutit.debug')


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

              | Q(shout__expiry_date__isnull=False, date_published__lte=F('shout__expiry_date'))
             )
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


def post_request(name, text, price, latitude, longitude, category, tags, shouter, country, city,
                 address="",
                 currency=DEFAULT_CURRENCY_CODE, images=None, videos=None, date_published=None,
                 is_sss=False, exp_days=None):
    return create_shout(POST_TYPE_REQUEST, name, text, price, latitude, longitude, category, tags,
                 shouter, country, city, address, currency, images, videos, date_published, is_sss,
                 exp_days)


def post_offer(name, text, price, latitude, longitude, category, tags, shouter, country, city,
               address="",
               currency=DEFAULT_CURRENCY_CODE, images=None, videos=None, date_published=None,
               is_sss=False, exp_days=None):
    return create_shout(POST_TYPE_OFFER, name, text, price, latitude, longitude, category, tags,
                 shouter, country, city, address, currency, images, videos, date_published, is_sss,
                 exp_days)


# todo: handle exception on each step and in case of errors, rollback!
def create_shout(shout_type, name, text, price, latitude, longitude, category, tags, shouter,
                 country, city, address="", currency=DEFAULT_CURRENCY_CODE, images=None,
                 videos=None,
                 date_published=None, is_sss=False, exp_days=None):

    item = item_controller.create_item(
        name=name, price=price, currency=currency, description=text, images=images, videos=videos)

    # if passed as [{'name': 'tag-x'},...]
    if tags:
        if not isinstance(tags[0], basestring):
            tags = [tag['name'] for tag in tags]
    # remove duplicates
    tags = list(OrderedDict.fromkeys(tags))

    shout = Shout(type=shout_type, text=text, user=shouter, category=category, tags=tags, item=item,
                  longitude=longitude, latitude=latitude, country=country, city=city,
                  address=address,
                  is_sss=is_sss)

    if date_published:
        shout.date_published = date_published
        shout.expiry_date = exp_days and (date_published + timedelta(days=exp_days)) or None
    else:
        shout.expiry_date = exp_days and datetime.today() + timedelta(days=exp_days) or None

    shout.save()
    shouter.profile.stream.add_post(shout)

    add_tags(tags, shout, shouter)
    add_pd_city(country, city, latitude, longitude)
    event_type = EVENT_TYPE_SHOUT_OFFER if shout_type == POST_TYPE_OFFER else EVENT_TYPE_SHOUT_REQUEST
    event_controller.register_event(shouter, event_type, shout)
    return shout


def add_tags(tags, shout, shouter):
    for tag in tag_controller.get_or_create_tags(tags, shouter):
        # prevent adding existing tags
        # todo: optimize
        try:
            tag.stream.add_post(shout)
        except IntegrityError:
            pass


def add_pd_city(country, city, latitude, longitude):
    encoded_city = to_seo_friendly(unicode.lower(unicode(city)))
    predefined_city = PredefinedCity.objects.filter(city=city)
    if not predefined_city:
        predefined_city = PredefinedCity.objects.filter(city_encoded=encoded_city)
    if not predefined_city:
        PredefinedCity(city=city, city_encoded=encoded_city, country=country, latitude=latitude,
                       longitude=longitude).save()


@receiver(post_save, sender=Shout)
def shout_index(sender, instance=None, created=False, **kwargs):
    shout = instance
    action = 'Created' if created else 'Updated'
    logger.debug('{} Shout: {}: {}, city: {}'.format(action, shout.pk, shout.item.name, shout.city))
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
    shout_index.city = shout.city
    shout_index.latitude = shout.latitude
    shout_index.longitude = shout.longitude
    shout_index.price = shout.item.price
    shout_index.uid = shout.user.pk
    shout_index.username = shout.user.username
    shout_index.date_published = shout.date_published
    shout_index.currency = shout.item.currency.code
    shout_index.address = shout.address
    shout_index.thumbnail = shout.thumbnail
    shout_index.video_url = shout.video_url
    if shout_index.save():
        logger.debug('Created ShoutIndex: %s.' % shout.pk)
    else:
        logger.debug('Updated ShoutIndex: %s.' % shout.pk)


def delete_shout_index(shout):
    try:
        shout_index = ShoutIndex.get(shout.pk)
        shout_index.delete()
        logger.debug('Deleted ShoutIndex: %s.' % shout.pk)
    except NotFoundError:
        logger.debug('ShoutIndex: %s not found.' % shout.pk)
    except ConflictError:
        logger.debug('ShoutIndex: %s already deleted.' % shout.pk)


# todo: check!
def EditShout(shout_id, name=None, text=None, price=None, latitude=None, longitude=None, tags=[],
              shouter=None, country=None,
              city=None, address=None, currency=None, images=[], date_published=None):
    shout = Shout.objects.get(pk=shout_id)

    if not shout:
        raise ObjectDoesNotExist()
    else:
        if shout.type == POST_TYPE_REQUEST or shout.type == POST_TYPE_OFFER:

            if text:
                shout.text = text
            if longitude:
                shout.longitude = longitude
            if latitude:
                shout.latitude = latitude
            if shouter:
                shout.shouter = shouter
            if city:
                shout.city = city
            if country:
                shout.country = country
            if address:
                shout.address = address
            if date_published:
                shout.date_published = date_published

            item_controller.edit_item(shout.item, name, price, images, currency)

            if len(tags) and shouter:
                shout.user = shouter
                shout.tags.clear()
                for tag in tag_controller.get_or_create_tags(tags, shouter):
                    # todo: optimize
                    try:
                        shout.tags.add(tag)
                        tag.stream.add_post(shout)
                    except IntegrityError:
                        pass

            return shout
    return None


from shoutit.controllers import tag_controller