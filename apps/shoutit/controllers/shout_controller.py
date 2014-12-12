from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.conf import settings

from common.constants import POST_TYPE_SELL, POST_TYPE_BUY, POST_TYPE_DEAL, POST_TYPE_EXPERIENCE
from common.constants import STREAM_TYPE_RECOMMENDED, STREAM_TYPE_RELATED
from common.constants import ACTIVITY_TYPE_SHOUT_SELL_CREATED, ACTIVITY_DATA_SHOUT
from common.constants import EVENT_TYPE_SHOUT_OFFER, EVENT_TYPE_SHOUT_REQUEST
from apps.shoutit.models import Shout, StoredImage, Stream, ShoutWrap, Trade, Post, PredefinedCity
from apps.shoutit.controllers import email_controller, stream_controller, event_controller, item_controller, realtime_controller
from apps.activity_logger.logger import Logger
from apps.shoutit.utils import asynchronous_task, to_seo_friendly


def GetPost(post_id, find_muted=False, find_expired=False):
    post = Post.objects.filter(pk__exact=post_id, IsDisabled=False).select_related('OwnerUser', 'OwnerUser__Business',
                                                                                   'OwnerBusiness__Profile')
    if not find_muted:
        post = post.filter(IsMuted=False)

    if not find_expired:
        today = datetime.today()
        days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
        begin = today - days
        post = post.filter(
            (~Q(Type=POST_TYPE_BUY) & ~Q(Type=POST_TYPE_SELL))
            |
            ((Q(shout__ExpiryDate__isnull=True, DatePublished__range=(begin, today))

              | Q(shout__ExpiryDate__isnull=False, DatePublished__lte=F('shout__ExpiryDate'))
             )
             & (Q(Type=POST_TYPE_BUY) | Q(Type=POST_TYPE_SELL)))
        ).select_related(depth=2)
    if post:
        post = post[0]
        if post.Type == POST_TYPE_SELL or post.Type == POST_TYPE_BUY:
            return post.shout.trade
        elif post.Type == POST_TYPE_EXPERIENCE:
            return post.experience
    else:
        return None


def DeletePost(post_id):
    post = Post.objects.get(pk=post_id)
    if not post:
        raise ObjectDoesNotExist()
    else:
        post.IsDisabled = True
        post.save()
        try:
            if post.Type == POST_TYPE_BUY or post.Type == POST_TYPE_SELL:
                event_controller.DeleteEventAboutObj(post.shout.trade)
            elif post.Type == POST_TYPE_DEAL:
                event_controller.DeleteEventAboutObj(post.shout.deal)
            elif post.Type == POST_TYPE_EXPERIENCE:
                event_controller.DeleteEventAboutObj(post.experience)
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


def EditShout(request, shout_id, name=None, text=None, price=None, latitude=None, longitude=None, tags=[], shouter=None, country_code=None,
              province_code=None, address=None, currency=None, images=[], date_published=None, stream=None):
    trade = Trade.objects.get(pk=shout_id)

    if not trade:
        raise ObjectDoesNotExist()
    else:
        if trade.Type == POST_TYPE_BUY or trade.Type == POST_TYPE_SELL:

            if text:
                trade.Text = text
            if longitude:
                trade.Longitude = longitude
            if latitude:
                trade.Latitude = latitude
            if shouter:
                trade.shouter = shouter
            if province_code:
                trade.ProvinceCode = province_code
            if country_code:
                trade.CountryCode = country_code
            if address:
                trade.Address = address
            if date_published:
                trade.DatePublished = date_published

            item_controller.edit_item(trade.trade.Item, name, price, images, currency)

            if stream and trade.Stream != stream:
                trade.Stream.UnPublishShout(trade)
                trade.Stream = stream
                stream.PublishShout(trade)

            if len(tags) and shouter:
                trade.OwnerUser = shouter
                trade.Tags.clear()
                for tag in tag_controller.GetOrCreateTags(request, tags, shouter):
                    trade.Tags.add(tag)
                    tag.Stream.PublishShout(trade)
            trade.StreamsCode = ','.join([str(f.pk) for f in trade.Streams.all()])
            trade.save()

            save_relocated_shouts(trade, STREAM_TYPE_RELATED)
            return trade
    return None


def get_shouts_in_view_port(down_left_lat, down_left_lng, up_right_lat, up_right_lng):
    filters = {
        'Latitude__gte': down_left_lat,
        'Latitude__lte': up_right_lat,
        'Longitude__gte': down_left_lng,
        'Longitude__lte': up_right_lng,
    }
    shouts = Trade.objects.GetValidTrades().filter(**filters).values('pk', 'Type', 'Longitude', 'Latitude', 'Item__Name')[:10000]
    return shouts


def get_shouts_and_points_in_view_port(down_left_lat, down_left_lng, up_right_lat, up_right_lng):
    if down_left_lng > up_right_lng:
        right_shouts = get_shouts_in_view_port(down_left_lat, -180.0, up_right_lat, up_right_lng)
        left_shouts = get_shouts_in_view_port(down_left_lat, down_left_lng, up_right_lat, 180.0)
        from itertools import chain

        shouts = list(chain(right_shouts, left_shouts))
    else:
        shouts = get_shouts_in_view_port(down_left_lat, down_left_lng, up_right_lat, up_right_lng)
    return shouts, [[shout['Latitude'], shout['Longitude']] for shout in shouts]


def GetStreamAffectedByShout(shout):
    if isinstance(shout, int):
        shout = Shout.objects.get(pk=shout)
    if shout:
        return shout.Streams.all()
    return []


@asynchronous_task()
def save_relocated_shouts(trade, stream_type):
    posts_type = POST_TYPE_BUY
    if stream_type == STREAM_TYPE_RECOMMENDED:
        if trade.Type == POST_TYPE_BUY:
            posts_type = POST_TYPE_SELL
        elif trade.Type == POST_TYPE_SELL:
            posts_type = POST_TYPE_BUY
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


def shout_buy(request, name, text, price, latitude, longitude, tags, shouter, country_code, province_code, address,
              currency, images=None, videos=None, date_published=None, stream=None, issss=False, exp_days=None):
    if stream is None:
        stream = shouter.profile.Stream

    item = item_controller.create_item(name=name, price=price, currency=currency, images=images, videos=videos)
    trade = Trade(Text=text, Longitude=longitude, Latitude=latitude, OwnerUser=shouter, Type=POST_TYPE_BUY, Item=item,
                  CountryCode=country_code, ProvinceCode=province_code, Address=address, IsSSS=issss)
    trade.save()

    #todo: check which to save encoded city or just normal. expectations are to get normal city from user
    encoded_city = to_seo_friendly(unicode.lower(unicode(province_code)))
    predefined_city = PredefinedCity.objects.filter(City=province_code)
    if not predefined_city:
            predefined_city = PredefinedCity.objects.filter(city_encoded=encoded_city)
    if not predefined_city:
        PredefinedCity(City=province_code, city_encoded=encoded_city, Country=country_code, Latitude=latitude, Longitude=longitude).save()

    if date_published:
        trade.DatePublished = date_published
        trade.ExpiryDate = exp_days and (date_published + timedelta(days=exp_days)) or None
        trade.save()
    else:
        trade.ExpiryDate = exp_days and datetime.today() + timedelta(days=exp_days) or None
        trade.save()

    stream.PublishShout(trade)
    for tag in tag_controller.GetOrCreateTags(request, tags, shouter):
        trade.Tags.add(tag)
        tag.Stream.PublishShout(trade)

    if trade:
        trade.StreamsCode = ','.join([str(f.pk) for f in trade.Streams.all()])
        trade.save()

    save_relocated_shouts(trade, STREAM_TYPE_RECOMMENDED)
    save_relocated_shouts(trade, STREAM_TYPE_RELATED)

    event_controller.RegisterEvent(shouter, EVENT_TYPE_SHOUT_REQUEST, trade)
    Logger.log(request, type=ACTIVITY_TYPE_SHOUT_SELL_CREATED, data={ACTIVITY_DATA_SHOUT: trade.pk})
    realtime_controller.BindUserToPost(shouter, trade)
    return trade


def shout_sell(request, name, text, price, latitude, longitude, tags, shouter, country_code, province_code, address,
               currency, images=None, videos=None, date_published=None, stream=None, issss=False, exp_days=None):
    if stream is None:
        stream = shouter.Stream

    item = item_controller.create_item(name=name, price=price, currency=currency, images=images, videos=videos)
    trade = Trade(Text=text, Longitude=longitude, Latitude=latitude, OwnerUser=shouter.user, Type=POST_TYPE_SELL,
                  Item=item, CountryCode=country_code, ProvinceCode=province_code, Address=address, IsSSS=issss)

    if date_published:
        trade.DatePublished = date_published
        trade.ExpiryDate = exp_days and (date_published + timedelta(days=exp_days)) or None
    else:
        trade.ExpiryDate = exp_days and datetime.today() + timedelta(days=exp_days) or None
    trade.save()

    encoded_city = to_seo_friendly(unicode.lower(unicode(province_code)))
    predefined_city = PredefinedCity.objects.filter(City=province_code)
    if not predefined_city:
            predefined_city = PredefinedCity.objects.filter(city_encoded=encoded_city)
    if not predefined_city:
        PredefinedCity(City=province_code, city_encoded=encoded_city, Country=country_code, Latitude=latitude, Longitude=longitude).save()

    stream.PublishShout(trade)
    for tag in tag_controller.GetOrCreateTags(request, tags, shouter.user):
        trade.Tags.add(tag)
        tag.Stream.PublishShout(trade)

    if trade:
        trade.StreamsCode = ','.join([str(f.pk) for f in trade.Streams.all()])
        trade.save()

    save_relocated_shouts(trade, STREAM_TYPE_RECOMMENDED)
    save_relocated_shouts(trade, STREAM_TYPE_RELATED)

    event_controller.RegisterEvent(shouter.user, EVENT_TYPE_SHOUT_OFFER, trade)
    Logger.log(request, type=ACTIVITY_TYPE_SHOUT_SELL_CREATED, data={ACTIVITY_DATA_SHOUT: trade.pk})
    realtime_controller.BindUserToPost(shouter.user, trade)
    return trade


def get_trade_images(trades):
    images = StoredImage.objects.filter(Shout__pk__in=[trade.pk for trade in trades]).order_by('Image').select_related('Item')
    for i in range(len(trades)):
        trades[i].Item.SetImages([image for image in images if image.Item_id == trades[i].Item.pk])
        images = [image for image in images if image.Item_id != trades[i].Item.pk]
    return trades

from apps.shoutit.controllers import tag_controller