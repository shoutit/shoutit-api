from collections import OrderedDict
from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.conf import settings

from shoutit.controllers.user_controller import get_profile
from common.constants import POST_TYPE_OFFER, POST_TYPE_REQUEST, POST_TYPE_EXPERIENCE, DEFAULT_CURRENCY_CODE
from common.constants import STREAM_TYPE_RECOMMENDED, STREAM_TYPE_RELATED
from common.constants import EVENT_TYPE_SHOUT_OFFER, EVENT_TYPE_SHOUT_REQUEST
from shoutit.models import Shout, StoredImage, Stream, ShoutWrap, Trade, Post, PredefinedCity
from shoutit.controllers import stream_controller, event_controller, email_controller, item_controller
from shoutit.utils import to_seo_friendly


def get_post(post_id, find_muted=False, find_expired=False):
    post = Post.objects.filter(id=post_id, is_disabled=False).select_related('user', 'user__Business', 'business__Profile')
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
            return post.shout.trade
        elif post.type == POST_TYPE_EXPERIENCE:
            return post.experience
    else:
        return None


def delete_post(post):
    post.is_disabled = True
    post.save()
    try:
        if post.type == POST_TYPE_REQUEST or post.type == POST_TYPE_OFFER:
            event_controller.delete_event_about_obj(post)
            # todo: check!
            # elif post.type == POST_TYPE_DEAL:
            # event_controller.delete_event_about_obj(post.shout.deal)
            # elif post.type == POST_TYPE_EXPERIENCE:
            # event_controller.delete_event_about_obj(post.experience)
    except:
        pass


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


def get_shouts_in_view_port(down_left_lat, down_left_lng, up_right_lat, up_right_lng, trade_objects=False):
    filters = {
        'latitude__gte': down_left_lat,
        'latitude__lte': up_right_lat,
        'longitude__gte': down_left_lng,
        'longitude__lte': up_right_lng,
    }
    if trade_objects:
        return Trade.objects.get_valid_trades().filter(**filters).select_related('item__Currency', 'user__profile')[:100]
    else:
        return Trade.objects.get_valid_trades().filter(**filters).values('pk', 'type', 'longitude', 'latitude', 'item__name')[:10000]


def get_shouts_and_points_in_view_port(down_left_lat, down_left_lng, up_right_lat, up_right_lng, shouts_only=False):
    if down_left_lng > up_right_lng:
        right_shouts = get_shouts_in_view_port(down_left_lat, -180.0, up_right_lat, up_right_lng, shouts_only)
        left_shouts = get_shouts_in_view_port(down_left_lat, down_left_lng, up_right_lat, 180.0, shouts_only)
        from itertools import chain

        # todo: check!
        shouts = chain(right_shouts, left_shouts) if shouts_only else list(chain(right_shouts, left_shouts))
    else:
        shouts = get_shouts_in_view_port(down_left_lat, down_left_lng, up_right_lat, up_right_lng, shouts_only)

    if shouts_only:
        return shouts
    else:
        return shouts, [[shout['latitude'], shout['longitude']] for shout in shouts]


def GetStreamAffectedByShout(shout):
    if isinstance(shout, int):
        shout = Shout.objects.get(pk=shout)
    if shout:
        return shout.Streams.all()
    return []


def save_relocated_shouts(trade, stream_type):
    if not trade or stream_type not in [STREAM_TYPE_RELATED, STREAM_TYPE_RECOMMENDED]:
        return

    posts_type = POST_TYPE_REQUEST
    if stream_type == STREAM_TYPE_RECOMMENDED:
        if trade.type == POST_TYPE_REQUEST:
            posts_type = POST_TYPE_OFFER
        elif trade.type == POST_TYPE_OFFER:
            posts_type = POST_TYPE_REQUEST
    elif stream_type == STREAM_TYPE_RELATED:
        posts_type = trade.type

    shouts = stream_controller.get_shout_recommended_shout_stream(trade, posts_type, 0, 10)
    stream = Stream(type=stream_type)
    stream.save()
    if stream_type == STREAM_TYPE_RECOMMENDED:
        old_recommended = trade.recommended_stream
        trade.recommended_stream = stream
        trade.save()
        if old_recommended:
            old_recommended.delete()
    elif stream_type == STREAM_TYPE_RELATED:
        old_related = trade.related_stream
        trade.related_stream = stream
        trade.save()
        if old_related:
            old_related.delete()
    for shout in shouts:
        shout_wrap = ShoutWrap(shout=shout, Stream=stream, rank=shout.rank)
        shout_wrap.save()
        stream_controller.PublishShoutToShout(trade, shout)

    trade.save()


# todo: handle exception on each step and in case of errors, rollback!
def post_request(name, text, price, latitude, longitude, tags, shouter, country, city, address="",
                 currency=DEFAULT_CURRENCY_CODE, images=None, videos=None, date_published=None, is_sss=False, exp_days=None):
    shouter_profile = get_profile(shouter.username)
    stream = shouter_profile.Stream
    stream2 = shouter_profile.stream2

    item = item_controller.create_item(name=name, price=price, currency=currency, description=text, images=images, videos=videos)
    trade = Trade(text=text, longitude=longitude, latitude=latitude, user=shouter, type=POST_TYPE_REQUEST, item=item,
                  country=country, city=city, address=address, is_sss=is_sss)
    trade.save()

    # todo: check which to save encoded city or just normal. expectations are to get normal city from user
    encoded_city = to_seo_friendly(unicode.lower(unicode(city)))
    predefined_city = PredefinedCity.objects.filter(city=city)
    if not predefined_city:
        predefined_city = PredefinedCity.objects.filter(city_encoded=encoded_city)
    if not predefined_city:
        PredefinedCity(city=city, city_encoded=encoded_city, country=country, latitude=latitude, longitude=longitude).save()

    if date_published:
        trade.date_published = date_published
        trade.expiry_date = exp_days and (date_published + timedelta(days=exp_days)) or None
        trade.save()
    else:
        trade.expiry_date = exp_days and datetime.today() + timedelta(days=exp_days) or None
        trade.save()

    stream.PublishShout(trade)
    stream2.add_post(trade)

    # if passed as [{'name': 'tag-x'},...]
    if tags:
        if not isinstance(tags[0], basestring):
            tags = [tag['name'] for tag in tags]
    # remove duplicates in case any
    tags = list(OrderedDict.fromkeys(tags))
    for tag in tag_controller.get_or_create_tags(tags, shouter):
        # prevent adding existing tags
        try:
            trade.tags.add(tag)
            tag.Stream.PublishShout(trade)
            tag.stream2.add_post(trade)
        except IntegrityError:
            pass

    if trade:
        trade.StreamsCode = ','.join([str(f.pk) for f in trade.Streams.all()])
        trade.save()

    save_relocated_shouts(trade, STREAM_TYPE_RECOMMENDED)
    save_relocated_shouts(trade, STREAM_TYPE_RELATED)

    event_controller.register_event(shouter, EVENT_TYPE_SHOUT_REQUEST, trade)
    return trade


# todo: handle exception on each step and in case of errors, rollback!
def post_offer(name, text, price, latitude, longitude, tags, shouter, country, city, address="",
               currency=DEFAULT_CURRENCY_CODE, images=None, videos=None, date_published=None, is_sss=False, exp_days=None):
    shouter_profile = get_profile(shouter.username)
    stream = shouter_profile.Stream
    stream2 = shouter_profile.stream2

    item = item_controller.create_item(name=name, price=price, currency=currency, description=text, images=images, videos=videos)
    trade = Trade(text=text, longitude=longitude, latitude=latitude, user=shouter, type=POST_TYPE_OFFER,
                  item=item, country=country, city=city, address=address, is_sss=is_sss)

    if date_published:
        trade.date_published = date_published
        trade.expiry_date = exp_days and (date_published + timedelta(days=exp_days)) or None
    else:
        trade.expiry_date = exp_days and datetime.today() + timedelta(days=exp_days) or None
    trade.save()

    encoded_city = to_seo_friendly(unicode.lower(unicode(city)))
    predefined_city = PredefinedCity.objects.filter(city=city)
    if not predefined_city:
        predefined_city = PredefinedCity.objects.filter(city_encoded=encoded_city)
    if not predefined_city:
        PredefinedCity(city=city, city_encoded=encoded_city, country=country, latitude=latitude, longitude=longitude).save()

    stream.PublishShout(trade)
    stream2.add_post(trade)

    # if passed as [{'name': 'tag-x'},...]
    if tags:
        if not isinstance(tags[0], basestring):
            tags = [tag['name'] for tag in tags]
    # remove duplicates in case any
    tags = list(OrderedDict.fromkeys(tags))
    for tag in tag_controller.get_or_create_tags(tags, shouter):
        # prevent adding existing tags
        try:
            trade.tags.add(tag)
            tag.Stream.PublishShout(trade)
            tag.stream2.add_post(trade)
        except IntegrityError:
            pass

    if trade:
        trade.StreamsCode = ','.join([str(f.pk) for f in trade.Streams.all()])
        trade.save()

    save_relocated_shouts(trade, STREAM_TYPE_RECOMMENDED)
    save_relocated_shouts(trade, STREAM_TYPE_RELATED)

    event_controller.register_event(shouter, EVENT_TYPE_SHOUT_OFFER, trade)
    return trade


# todo: check!
def EditShout(shout_id, name=None, text=None, price=None, latitude=None, longitude=None, tags=[], shouter=None, country=None,
              city=None, address=None, currency=None, images=[], date_published=None):
    trade = Trade.objects.get(pk=shout_id)

    if not trade:
        raise ObjectDoesNotExist()
    else:
        if trade.type == POST_TYPE_REQUEST or trade.type == POST_TYPE_OFFER:

            if text:
                trade.text = text
            if longitude:
                trade.longitude = longitude
            if latitude:
                trade.latitude = latitude
            if shouter:
                trade.shouter = shouter
            if city:
                trade.city = city
            if country:
                trade.country = country
            if address:
                trade.address = address
            if date_published:
                trade.date_published = date_published

            item_controller.edit_item(trade.trade.item, name, price, images, currency)

            if len(tags) and shouter:
                trade.user = shouter
                trade.tags.clear()
                for tag in tag_controller.get_or_create_tags(tags, shouter):
                    try:
                        trade.tags.add(tag)
                        tag.Stream.PublishShout(trade)
                        tag.stream2.add_post(trade)
                    except IntegrityError:
                        pass
            trade.StreamsCode = ','.join([str(f.pk) for f in trade.Streams.all()])
            trade.save()

            save_relocated_shouts(trade, STREAM_TYPE_RELATED)
            return trade
    return None


def get_trade_images(trades):
    images = StoredImage.objects.filter(shout__pk__in=[trade.pk for trade in trades]).order_by('image').select_related('item')
    for i in range(len(trades)):
        trades[i].item.set_images([image for image in images if image.item_id == trades[i].item.pk])
        images = [image for image in images if image.item_id != trades[i].item.pk]
    return trades


from shoutit.controllers import tag_controller