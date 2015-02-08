from collections import OrderedDict
from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.conf import settings
from apps.shoutit.controllers.user_controller import get_profile

from common.constants import POST_TYPE_OFFER, POST_TYPE_REQUEST, POST_TYPE_DEAL, POST_TYPE_EXPERIENCE, DEFAULT_CURRENCY_CODE
from common.constants import STREAM_TYPE_RECOMMENDED, STREAM_TYPE_RELATED
from common.constants import EVENT_TYPE_SHOUT_OFFER, EVENT_TYPE_SHOUT_REQUEST
from apps.shoutit.models import Shout, StoredImage, Stream, ShoutWrap, Trade, Post, PredefinedCity
from apps.shoutit.controllers import email_controller, stream_controller, event_controller, item_controller, realtime_controller
from apps.shoutit.utils import to_seo_friendly


def get_post(post_id, find_muted=False, find_expired=False):
    post = Post.objects.filter(id=post_id, IsDisabled=False).select_related('OwnerUser', 'OwnerUser__Business', 'OwnerBusiness__Profile')
    if not find_muted:
        post = post.filter(IsMuted=False)

    if not find_expired:
        today = datetime.today()
        days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
        begin = today - days
        post = post.filter(
            (~Q(Type=POST_TYPE_REQUEST) & ~Q(Type=POST_TYPE_OFFER))
            |
            ((Q(shout__ExpiryDate__isnull=True, DatePublished__range=(begin, today))

              | Q(shout__ExpiryDate__isnull=False, DatePublished__lte=F('shout__ExpiryDate'))
             )
             & (Q(Type=POST_TYPE_REQUEST) | Q(Type=POST_TYPE_OFFER)))
        ).select_related()
    if post:
        post = post[0]
        if post.Type == POST_TYPE_OFFER or post.Type == POST_TYPE_REQUEST:
            return post.shout.trade
        elif post.Type == POST_TYPE_EXPERIENCE:
            return post.experience
    else:
        return None


def delete_post(post):
    post.IsDisabled = True
    post.save()
    try:
        if post.Type == POST_TYPE_REQUEST or post.Type == POST_TYPE_OFFER:
            event_controller.delete_event_about_obj(post)
            # todo: check!
            # elif post.Type == POST_TYPE_DEAL:
            # event_controller.delete_event_about_obj(post.shout.deal)
            # elif post.Type == POST_TYPE_EXPERIENCE:
            # event_controller.delete_event_about_obj(post.experience)
    except:
        pass


def RenewShout(request, shout_id, days=int(settings.MAX_EXPIRY_DAYS)):
    shout = Shout.objects.get(pk=shout_id)
    if not shout:
        raise ObjectDoesNotExist()
    else:
        now = datetime.now()
        shout.DatePublished = now
        shout.ExpiryDate = now + timedelta(days=days)
        shout.RenewalCount += 1
        shout.ExpiryNotified = False
        shout.save()


def NotifyPreExpiry():
    shouts = Shout.objects.all()
    for shout in shouts:
        if not shout.ExpiryNotified:
            expiry_date = shout.ExpiryDate
            if not expiry_date:
                expiry_date = shout.DatePublished + timedelta(days=settings.MAX_EXPIRY_DAYS)
            if (expiry_date - datetime.now()).days < settings.SHOUT_EXPIRY_NOTIFY:
                if shout.OwnerUser.email:
                    email_controller.SendExpiryNotificationEmail(shout.OwnerUser, shout)
                    shout.ExpiryNotified = True
                    shout.save()


# todo: check!
def EditShout(shout_id, name=None, text=None, price=None, latitude=None, longitude=None, tags=[], shouter=None, country=None,
              city=None, address=None, currency=None, images=[], date_published=None):
    trade = Trade.objects.get(pk=shout_id)

    if not trade:
        raise ObjectDoesNotExist()
    else:
        if trade.Type == POST_TYPE_REQUEST or trade.Type == POST_TYPE_OFFER:

            if text:
                trade.Text = text
            if longitude:
                trade.Longitude = longitude
            if latitude:
                trade.Latitude = latitude
            if shouter:
                trade.shouter = shouter
            if city:
                trade.ProvinceCode = city
            if country:
                trade.CountryCode = country
            if address:
                trade.Address = address
            if date_published:
                trade.DatePublished = date_published

            item_controller.edit_item(trade.trade.Item, name, price, images, currency)

            if len(tags) and shouter:
                trade.OwnerUser = shouter
                trade.Tags.clear()
                for tag in tag_controller.get_or_create_tags(tags, shouter):
                    try:
                        trade.Tags.add(tag)
                        tag.Stream.PublishShout(trade)
                        tag.stream2.add_post(trade)
                    except IntegrityError:
                        pass
            trade.StreamsCode = ','.join([str(f.pk) for f in trade.Streams.all()])
            trade.save()

            save_relocated_shouts(trade, STREAM_TYPE_RELATED)
            return trade
    return None


def get_shouts_in_view_port(down_left_lat, down_left_lng, up_right_lat, up_right_lng, trade_objects=False):
    filters = {
        'Latitude__gte': down_left_lat,
        'Latitude__lte': up_right_lat,
        'Longitude__gte': down_left_lng,
        'Longitude__lte': up_right_lng,
    }
    if trade_objects:
        return Trade.objects.get_valid_trades().filter(**filters).select_related('Item__Currency', 'OwnerUser__profile')[:100]
    else:
        return Trade.objects.get_valid_trades().filter(**filters).values('pk', 'Type', 'Longitude', 'Latitude', 'Item__Name')[:10000]


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
        return shouts, [[shout['Latitude'], shout['Longitude']] for shout in shouts]


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
        if trade.Type == POST_TYPE_REQUEST:
            posts_type = POST_TYPE_OFFER
        elif trade.Type == POST_TYPE_OFFER:
            posts_type = POST_TYPE_REQUEST
    elif stream_type == STREAM_TYPE_RELATED:
        posts_type = trade.Type

    shouts = stream_controller.get_shout_recommended_shout_stream(trade, posts_type, 0, 10, stream_type == STREAM_TYPE_RECOMMENDED)
    stream = Stream(Type=stream_type)
    stream.save()
    if stream_type == STREAM_TYPE_RECOMMENDED:
        old_recommended = trade.RecommendedStream
        trade.RecommendedStream = stream
        trade.save()
        if old_recommended:
            old_recommended.delete()
    elif stream_type == STREAM_TYPE_RELATED:
        old_related = trade.RelatedStream
        trade.RelatedStream = stream
        trade.save()
        if old_related:
            old_related.delete()
    for shout in shouts:
        shout_wrap = ShoutWrap(Shout=shout, Stream=stream, Rank=shout.rank)
        shout_wrap.save()
        stream_controller.PublishShoutToShout(trade, shout)

    trade.save()


def post_request(name, text, price, latitude, longitude, tags, shouter, country, city, address="",
                 currency=DEFAULT_CURRENCY_CODE, images=None, videos=None, date_published=None, is_sss=False, exp_days=None):
    shouter_profile = get_profile(shouter.username)
    stream = shouter_profile.Stream
    stream2 = shouter_profile.stream2

    item = item_controller.create_item(name=name, price=price, currency=currency, description=text, images=images, videos=videos)
    trade = Trade(Text=text, Longitude=longitude, Latitude=latitude, OwnerUser=shouter, Type=POST_TYPE_REQUEST, Item=item,
                  CountryCode=country, ProvinceCode=city, Address=address, IsSSS=is_sss)
    trade.save()

    # todo: check which to save encoded city or just normal. expectations are to get normal city from user
    encoded_city = to_seo_friendly(unicode.lower(unicode(city)))
    predefined_city = PredefinedCity.objects.filter(City=city)
    if not predefined_city:
        predefined_city = PredefinedCity.objects.filter(city_encoded=encoded_city)
    if not predefined_city:
        PredefinedCity(City=city, city_encoded=encoded_city, Country=country, Latitude=latitude, Longitude=longitude).save()

    if date_published:
        trade.DatePublished = date_published
        trade.ExpiryDate = exp_days and (date_published + timedelta(days=exp_days)) or None
        trade.save()
    else:
        trade.ExpiryDate = exp_days and datetime.today() + timedelta(days=exp_days) or None
        trade.save()

    stream.PublishShout(trade)
    stream2.add_post(trade)

    for tag in tag_controller.get_or_create_tags(tags, shouter):
        trade.Tags.add(tag)
        tag.Stream.PublishShout(trade)
        tag.stream2.add_post(trade)

    if trade:
        trade.StreamsCode = ','.join([str(f.pk) for f in trade.Streams.all()])
        trade.save()

    save_relocated_shouts(trade, STREAM_TYPE_RECOMMENDED)
    save_relocated_shouts(trade, STREAM_TYPE_RELATED)

    event_controller.register_event(shouter, EVENT_TYPE_SHOUT_REQUEST, trade)
    realtime_controller.BindUserToPost(shouter, trade)
    return trade


# todo: handle exception on each step and in case of errors, rollback!
def post_offer(name, text, price, latitude, longitude, tags, shouter, country, city, address="",
               currency=DEFAULT_CURRENCY_CODE, images=None, videos=None, date_published=None, is_sss=False, exp_days=None):
    shouter_profile = get_profile(shouter.username)
    stream = shouter_profile.Stream
    stream2 = shouter_profile.stream2

    item = item_controller.create_item(name=name, price=price, currency=currency, description=text, images=images, videos=videos)
    trade = Trade(Text=text, Longitude=longitude, Latitude=latitude, OwnerUser=shouter, Type=POST_TYPE_OFFER,
                  Item=item, CountryCode=country, ProvinceCode=city, Address=address, IsSSS=is_sss)

    if date_published:
        trade.DatePublished = date_published
        trade.ExpiryDate = exp_days and (date_published + timedelta(days=exp_days)) or None
    else:
        trade.ExpiryDate = exp_days and datetime.today() + timedelta(days=exp_days) or None
    trade.save()

    encoded_city = to_seo_friendly(unicode.lower(unicode(city)))
    predefined_city = PredefinedCity.objects.filter(City=city)
    if not predefined_city:
        predefined_city = PredefinedCity.objects.filter(city_encoded=encoded_city)
    if not predefined_city:
        PredefinedCity(City=city, city_encoded=encoded_city, Country=country, Latitude=latitude, Longitude=longitude).save()

    stream.PublishShout(trade)
    stream2.add_post(trade)

    # remove duplicates in case any
    tags = list(OrderedDict.fromkeys(tags))
    for tag in tag_controller.get_or_create_tags(tags, shouter):
        # prevent adding existing tags
        try:
            trade.Tags.add(tag)
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
    realtime_controller.BindUserToPost(shouter, trade)
    return trade


def get_trade_images(trades):
    images = StoredImage.objects.filter(Shout__pk__in=[trade.pk for trade in trades]).order_by('image').select_related('Item')
    for i in range(len(trades)):
        trades[i].Item.set_images([image for image in images if image.Item_id == trades[i].Item.pk])
        images = [image for image in images if image.Item_id != trades[i].Item.pk]
    return trades


from apps.shoutit.controllers import tag_controller