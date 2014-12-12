from datetime import datetime, timedelta
import time

from django.db import connection
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.conf import settings

from common.constants import STREAM_TYPE_RELATED, STREAM_TYPE_RECOMMENDED, DEFAULT_PAGE_SIZE, PRICE_RANK_TYPE, POST_TYPE_EXPERIENCE, \
    POST_TYPE_BUY, POST_TYPE_SELL, FOLLOW_RANK_TYPE, DISTANCE_RANK_TYPE, TIME_RANK_TYPE, STREAM2_TYPE_PROFILE, STREAM2_TYPE_TAG
from apps.shoutit.models import Stream, ShoutWrap, Shout, Tag, StoredImage, Trade, Stream2, Listen, Profile
from apps.shoutit import utils


def PublishShoutToShout(shout, other):
    rank = 0.0
    distance = utils.normalized_distance(shout.Latitude, shout.Longitude, other.Latitude, other.Longitude)
    if distance > other.MaxDistance:
        other.MaxDistance = distance
        other.save()
    rank += distance / other.MaxDistance
    followings = utils.mutual_followings(shout.StreamsCode, other.StreamsCode)
    if followings > other.MaxFollowings:
        other.MaxFollowings = followings
        other.save()
    rank += 1 - (followings / other.MaxFollowings)
    rank /= 2
    if shout.Type == other.Type:
        if other.RelatedStream is None:
            other.RelatedStream = Stream(Type=STREAM_TYPE_RELATED)
            other.RelatedStream.save()
            other.save()
        if other.RelatedStream.ShoutWraps.filter(Shout=shout).count():
            other.RelatedStream.ShoutWraps.filter(Shout=shout).delete()
        shout_wrap = ShoutWrap(Shout=shout, Stream=other.RelatedStream, Rank=rank)
        shout_wrap.save()
    else:
        if other.RecommendedStream is None:
            other.RecommendedStream = Stream(Type=STREAM_TYPE_RECOMMENDED)
            other.RecommendedStream.save()
            other.save()
        if other.RecommendedStream.ShoutWraps.filter(Shout=shout).count():
            other.RecommendedStream.ShoutWraps.filter(Shout=shout).delete()
        shout_wrap = ShoutWrap(Shout=shout, Stream=other.RecommendedStream, Rank=rank)
        shout_wrap.save()
    return rank


def MaxFollowings(pks, country_code, province_code, filters):
    shouts = Trade.objects.GetValidTrades(country_code=country_code, province_code=province_code).filter(**filters)
    shouts = shouts.select_related('Streams').filter(Streams__pk__in=pks).values('StreamsCode')
    mutuals = [len(set(f for f in shout['StreamsCode'].split(',') if len(shout['StreamsCode'].strip()) > 0) & set(pks))
               for shout in shouts]
    return max(mutuals) if mutuals else 0


def MaxDistance(points, lat, lng):
    max_distance = 180
    if len(points) > 0:
        codes = [[float(point['Latitude']), float(point['Longitude'])] for point in points]
        observation = [float(lat), float(lng)]
        farest_index = utils.get_farest_point(observation, codes)
        farest_point = points[farest_index]
        max_distance = utils.normalized_distance(farest_point['Latitude'], farest_point['Longitude'], lat, lng)

    return max_distance


def GetShoutTimeOrder(pk, country_code, province_code, limit=0):
    shout_qs = Trade.objects.GetValidTrades(country_code=country_code, province_code=province_code).order_by('-DatePublished')
    shout_qs = shout_qs.values('pk')
    shouts = list(shout_qs)
    shouts = [shout['pk'] for shout in shouts]
    try:
        index = shouts.index(pk)
        return index > DEFAULT_PAGE_SIZE and DEFAULT_PAGE_SIZE or index
    except ValueError, e:
        return 0


def get_ranked_shouts_ids(user, rank_type_flag, country_code='', province_code='', lat=0.0, lng=0.0, start_index=None, end_index=None,
                          filter_types=[], filter_query=None, filter_tags=[]):
    # Selects shout IDs from database in the right order.
    # ---------------------------------------------------
    #		user: the User displaying shouts.
    #		rank_type_flag: determines the combination of the types of ranking you like to do.. (see constants.py).
    #		country_code, province_code: filtering criteria.
    #		lat, lng: current location.
    #		start_index, end index: filtering criteria.
    #		filter_types: array of types you like to filter on(see constants.py for types).
    #		filter_query: a search string, work on shout item name and shout text.
    #		filter_tags: array of tags you like to filter on.
    #		RETURNS: array of tuple(shout pk, shout rank).

    # initializing variables
    user_followings_pks = []
    if user is not None:
        #     user_followings_pks = [x['pk'] for x in Stream.objects.filter(followship__follower=user.profile).values('pk')]  # todo: check!
        user_followings_pks = [stream['pk'] for stream in Stream2.objects.filter(listen__listener=user).values('pk')]

    where_custom_clause = []
    additional_selects = []
    group_by_string = ''

    filters = {
        'IsMuted__exact': False,
        'IsDisabled__exact': False
    }

    # Types filtering
    if filter_types is not None and len(filter_types) > 0:
        filters['Type__in'] = filter_types
        if int(rank_type_flag & PRICE_RANK_TYPE) and filters['Type__in'].count(POST_TYPE_EXPERIENCE):
            filters['Type__in'].remove(POST_TYPE_EXPERIENCE)
    else:
        if int(rank_type_flag & PRICE_RANK_TYPE):
            filters['Type__in'] = [POST_TYPE_BUY, POST_TYPE_SELL]

    if filter_tags is not None and len(filter_tags) > 0:
        if 'Tags__pk__in' in filters:
            filters['Tags__pk__in'].extend(filter_tags)
        else:
            filters['Tags__pk__in'] = filter_tags

    # initializing current and base time variables
    today = datetime.today()
    days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
    begin = today - days

    base_timestamp = int(time.mktime(begin.utctimetuple()))
    now_timestamp = int(time.mktime(datetime.now().utctimetuple()))
    now_timestamp_string = str(datetime.now())

    extra_order_bys = ''
    rank_count = 0

    # building the queryset
    shout_qs = Shout.objects.select_related('Item', 'Item__Currency', 'OwnerUser', 'OwnerUser__Profile', 'Tags').filter(**filters)

    # Calculating the stream following rank attribute
    if int(rank_type_flag & FOLLOW_RANK_TYPE):
        if user is not None:
            max_followings = MaxFollowings(user_followings_pks, country_code, province_code, filters)
            #todo: find way to join tables
            #_connection = (None, Shout._meta.db_table, None)
            #shout_qs.query.join(connection=_connection)
            #_connection = (
            #    Shout._meta.db_table,
            #    Shout.Streams.field.m2m_db_table(),
            #    ((Shout._meta.pk.column, Shout.Streams.field.m2m_column_name()),)
            #)
            #jf = Shout.Streams.field.rel
            #shout_qs.query.join(connection=_connection, join_field=jf)
            if max_followings > 0:
                extra_order_bys += 'power( ' + str(settings.RANK_COEFFICIENT_FOLLOW) + \
                                   ' * ( 1 - (CAST(COUNT("shoutit_post_Streams"."stream_id") ' \
                                   'AS DOUBLE PRECISION) / CAST(%d AS DOUBLE PRECISION))), 2.0) + ' % max_followings
                rank_count += 1
            group_by_string = '"shoutit_shout"."post_ptr_id"'

    # Calculating the Distance rank attribute:
    if int(rank_type_flag & DISTANCE_RANK_TYPE):
        # A temporary solution for max distance:
        points = list(Shout.objects.filter(**filters).values('Latitude', 'Longitude'))
        if lat is not None and lng is not None:
            max_distance = MaxDistance(points, lat, lng)
            if max_distance > 0.0:
                extra_order_bys += 'power( ' + str(settings.RANK_COEFFICIENT_DISTANCE) + \
                                   ' * (normalized_distance("shoutit_post"."Latitude", "shoutit_post"."Longitude", ' \
                                   'CAST(%f as DOUBLE PRECISION), CAST(%f as DOUBLE PRECISION)) / ' \
                                   'CAST(%.100f as DOUBLE PRECISION)' \
                                   '), 2.0) + ' % (float(lat), float(lng), max_distance)
                rank_count += 1
            if group_by_string != '':
                group_by_string += ', "shoutit_post"."Latitude", "shoutit_post"."Longitude"'

    # Calculating the Time rank attribute:
    if int(rank_type_flag & TIME_RANK_TYPE):
        extra_order_bys += 'power( ' + str(
            settings.RANK_COEFFICIENT_TIME) + ' * (extract (epoch from age(\'%s\', "shoutit_post"."DatePublished"))/ %d), 2.0) + ' % (
            now_timestamp_string, now_timestamp - base_timestamp)
        rank_count += 1
        if group_by_string != '':
            group_by_string += ', "shoutit_post"."DatePublished"'

    # Calculating the Price rank attribute
    if int(rank_type_flag & PRICE_RANK_TYPE):
        extra_order_bys += '("Price"/(SELECT MAX("Price") FROM "shoutit_item")) + '
        rank_count += 1

    if rank_count:
        extra_order_bys = extra_order_bys.strip()
        extra_order_bys = '(|/(' + extra_order_bys[:-1] + ')) / |/(%d)' % rank_count
    else:
        extra_order_bys = ''

    # applying filters if a search query exists (applying by SQL string, not on Django models)
    if filter_query:
        item_name_q = ''
        text_q = ''
        for keyword in filter_query.split(' '):
            keyword = utils.safe_sql(keyword)
            if item_name_q != '':
                item_name_q += "AND UPPER(\"shoutit_item\".\"Name\"::text) LIKE UPPER(E'%%%%%%%%%s%%%%%%%%')" % keyword
                text_q += "AND UPPER(\"shoutit_post\".\"Text\"::text) LIKE UPPER(E'%%%%%%%%%s%%%%%%%%')" % keyword
            else:
                item_name_q = "UPPER(\"shoutit_item\".\"Name\"::text) LIKE UPPER(E'%%%%%%%%%s%%%%%%%%')" % keyword
                text_q = "UPPER(\"shoutit_post\".\"Text\"::text) LIKE UPPER(E'%%%%%%%%%s%%%%%%%%')" % keyword
        where_custom_clause.append('((' + item_name_q + ') OR (' + text_q + '))')
        additional_selects.append('trade__Item__Name')
        if group_by_string != '':
            group_by_string += ', "shoutit_item"."Name"'

    # completing WHERE part of the SQL query string and merge it into the QuerySet
    where_custom_clause.append(
        '(("shoutit_shout"."ExpiryDate" IS NULL AND "shoutit_post"."DatePublished" BETWEEN \'%s\' AND \'%s\') OR ("shoutit_shout"."ExpiryDate" IS NOT NULL AND now() < "shoutit_shout"."ExpiryDate"))' % (
            str(begin), str(today)))
    if country_code and country_code <> '':
        where_custom_clause.append('"shoutit_post"."CountryCode" = \'%s\'' % country_code)
    if province_code and province_code <> '':
        where_custom_clause.append('LOWER("shoutit_post"."ProvinceCode") = \'%s\'' % unicode.lower(u'' + province_code))
    shout_qs = shout_qs.extra(where=where_custom_clause)

    if extra_order_bys != '':
        shout_qs = shout_qs.distinct().extra(select={'rank': extra_order_bys}).extra(order_by=['rank'])[start_index:end_index]
    else:
        shout_qs = shout_qs.distinct().order_by('-DatePublished')[start_index:end_index]

    # extracting the raw SQl from the QuerySet
    query_string = unicode(shout_qs.values('pk', 'rank', *additional_selects).query)
    index = (query_string.find('ORDER BY') - 1)
    if group_by_string != '':
        query_string = unicode(query_string[:index]) + ' GROUP BY ' + group_by_string + ' ' + str(query_string[index:])

    #todo: find way to join tables
    qp = ' LEFT OUTER JOIN "shoutit_post_Streams" ON ("shoutit_shout"."post_ptr_id" = "shoutit_post_Streams"."post_id") '
    if int(rank_type_flag & FOLLOW_RANK_TYPE):
        if user is not None:
            where_index = query_string.find('WHERE')
            query_string = unicode(query_string[:where_index]) + unicode(qp) + unicode(query_string[where_index:])

    if int(rank_type_flag & FOLLOW_RANK_TYPE):
        if len(user_followings_pks):
            index = (query_string.find(qp) + len(qp))
            query_string = \
                unicode(query_string[:index]) + ' and "shoutit_post_Streams"."stream_id" IN (%s) ' % unicode(user_followings_pks)[
                                                                                                     1:-1] + unicode(query_string[index:])

    # executing query SQL & fetching shout IDs
    cursor = connection.cursor()
    cursor.execute(' '' ' + query_string + ' '' ')
    return [(str(row[1]), row[0]) for row in cursor.fetchall() if row and len(row)]


def get_shout_recommended_shout_stream(base_shout, type, start_index=None, end_index=None, exclude_shouter=True):
    filters = {}

    today = datetime.today()
    days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
    begin = today - days
    filters['Type'] = int(type)
    filters['Tags__pk__in'] = [t.pk for t in base_shout.GetTags()]

    base_timestamp = int(time.mktime(begin.utctimetuple()))
    now_timestamp = int(time.mktime(datetime.now().utctimetuple()))
    now_timestamp_string = str(datetime.now())

    extra_order_bys = ''
    points = list(
        Trade.objects.GetValidTrades(country_code=base_shout.CountryCode, province_code=base_shout.ProvinceCode).filter(**filters).values(
            'Latitude', 'Longitude'))
    max_distance = MaxDistance(points, float(base_shout.Latitude), float(base_shout.Longitude))
    pks = [x for x in base_shout.StreamsCode.split(',')]
    max_followings = MaxFollowings(pks, base_shout.CountryCode, base_shout.ProvinceCode, filters)

    extra_order_bys += 'power( ' + str(
        settings.RANK_COEFFICIENT_TIME) + ' * (extract (epoch from age(\'%s\', "shoutit_post"."DatePublished"))/ %d), 2.0) + ' % (
        now_timestamp_string, now_timestamp - base_timestamp)
    rank_count = 1

    if max_distance > 0.0:
        extra_order_bys += 'power( ' + str(
            settings.RANK_COEFFICIENT_TIME) + ' * (normalized_distance("shoutit_post"."Latitude", "shoutit_post"."Longitude", CAST(%f as DOUBLE PRECISION), CAST(%f as DOUBLE PRECISION)) / CAST(%.100f as DOUBLE PRECISION)), 2.0) + ' % (
            float(base_shout.Latitude), float(base_shout.Longitude), max_distance)
        rank_count += 1
        base_shout.MaxDistance = max_distance
        base_shout.save()

    if max_followings > 0:
        extra_order_bys += 'power( ' + str(
            settings.RANK_COEFFICIENT_TIME) + ' * (1 - (CAST(get_followings(\'%s\', "shoutit_trade"."StreamsCode") AS DOUBLE PRECISION) / CAST(%d AS DOUBLE PRECISION))), 2.0) + ' % (
            base_shout.StreamsCode, max_followings)
        rank_count += 1
        base_shout.MaxFollowings = max_followings
        base_shout.save()

    extra_order_bys = '(|/(' + extra_order_bys.strip()[:-1] + ')) / |/(%d)' % rank_count

    shout_qs = Trade.objects.GetValidTrades(country_code=base_shout.CountryCode, province_code=base_shout.ProvinceCode).select_related(
        'Item', 'Item__Currency', 'OwnerUser__Profile', 'Tags').filter(**filters).filter(~Q(pk=base_shout.pk))
    if exclude_shouter:
        shout_qs = shout_qs.filter(~Q(OwnerUser=base_shout.OwnerUser))
    shout_qs = shout_qs.extra(select={'time_rank': '(extract (epoch from age(\'%s\', "shoutit_post"."DatePublished"))/ %d)' % (
        now_timestamp_string, now_timestamp - base_timestamp)})
    shout_qs = shout_qs.extra(select={'rank': extra_order_bys}).extra(order_by=['rank'])[start_index:end_index]

    return attach_related_to_shouts(shout_qs, rank_count)


def get_trades_by_pks(pks):
    """
    Select shouts from database according to their IDs, including other objects related to every shout.
    pks: array of shout IDs
    return: array of shout objects
    """
    if not pks:
        return []
    #todo: choose which statement with less queries and enough data
    #shout_qs = Trade.objects.GetValidTrades().select_related('Item', 'Item__Currency', 'OwnerUser', 'OwnerUser__Profile').prefetch_related('Tags','Item__Images').filter(pk__in = pks)
    #shout_qs = Trade.objects.GetValidTrades().select_related('Item', 'Item__Currency', 'OwnerUser', 'OwnerUser__Profile','Tags').filter(pk__in = pks)
    shout_qs = Trade.objects.GetValidTrades().select_related('Item', 'Item__Currency', 'OwnerUser', 'OwnerUser__Profile').filter(pk__in=pks)

    return attach_related_to_shouts(shout_qs)


def attach_related_to_shouts(shouts, rank_count=None):
    """
    attach tags and images to the shouts to minimize the database queries
    """
    if len(shouts):
        tags = Tag.objects.select_related('Creator').prefetch_related('Shouts')
        tags = tags.extra(where=['shout_id IN (%s)' % ','.join(["'%s'" % str(shout.pk) for shout in shouts])])
        tags_with_shout_id = list(tags.values('pk', 'Name', 'Creator', 'Image', 'DateCreated', 'Definition', 'Shouts__pk'))

        images = StoredImage.objects.filter(Q(Shout__pk__in=[shout.pk for shout in shouts if shout.Type == POST_TYPE_EXPERIENCE]) | Q(
            Item__pk__in=[shout.Item.pk for shout in shouts if shout.Type != POST_TYPE_EXPERIENCE])).order_by('Image')

        for shout in shouts:
            if rank_count:
                shout.rank = ((shout.rank ** 2) * rank_count - shout.time_rank) / (rank_count - 1)

            shout.SetTags([tag for tag in tags_with_shout_id if str(tag['Shouts__pk']) == shout.pk])
            tags_with_shout_id = [tag for tag in tags_with_shout_id if str(tag['Shouts__pk']) != shout.pk]

            shout.Item.SetImages([image for image in images if image.Item.pk == shout.Item.pk])
            # reducing the images main array
            images = [image for image in images if image.Item.pk != shout.Item.pk]

    return list(shouts)


def get_ranked_stream_shouts(stream):
    today = datetime.today()
    days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
    begin = today - days
    base_timestamp = int(time.mktime(begin.utctimetuple()))
    now_timestamp = int(time.mktime(datetime.now().utctimetuple()))
    now_timestamp_string = str(datetime.now())

    time_axis = '(extract (epoch from age(\'%s\', "shoutit_post"."DatePublished"))/ %d)' % (
        now_timestamp_string, now_timestamp - base_timestamp)

    shouts = stream.ShoutWraps.select_related('Shout', 'Trade').filter(
        Q(Shout__ExpiryDate__isnull=True, Shout__DatePublished__range=(begin, today)) | Q(Shout__ExpiryDate__isnull=False,
                                                                                          Shout__DatePublished__lte=F(
                                                                                              'Shout__ExpiryDate')),
        Shout__IsMuted=False, Shout__IsDisabled=False).extra(select={'overall_rank': '(("Rank" * 2) + %s) / 3' % time_axis}).extra(
        order_by=['overall_rank'])
    if not shouts:
        return []
    return [shout.Shout.trade for shout in shouts]


# todo: use country, city, etc
def get_stream_shouts(stream, start_index=0, end_index=DEFAULT_PAGE_SIZE, show_expired=False, country=None, city=None):
    """
    return the shouts (offers/requests) in a stream
    """
    post_pks = [post['pk'] for post in stream.Posts.filter(Type__in=[POST_TYPE_BUY, POST_TYPE_SELL]).order_by('-DatePublished').values('pk')[start_index:end_index]]
    trades = Trade.objects.filter(pk__in=post_pks).order_by('-DatePublished')
    return attach_related_to_shouts(trades)


def get_stream_shouts_count(stream):
    """
    return the total number of shouts (offers/requests) in a stream
    """
    return stream.Posts.filter(Type__in=[POST_TYPE_BUY, POST_TYPE_SELL]).count()


def get_stream_listeners(stream, count_only=False):
    """
    return the users who are listening to this stream
    """
    if count_only:
        listeners = stream.listeners.count()
    else:
        listeners = stream.listeners.all()
    return listeners


def get_user_listening(user, stream_type=None, count_only=False):
    """
    return the objects (Profiles, Tags, etc) that the users are listening to their streams
    """
    if stream_type:
        qs = Listen.objects.filter(listener=user, stream__type=stream_type)
    else:
        qs = Listen.objects.filter(listener=user)

    if count_only:
        return qs.count()
    else:
        listens = qs.all()
        stream_pks = [listen.stream_id for listen in listens]
        streams = Stream2.objects.filter(pk__in=stream_pks)
        object_ids = [stream.object_id for stream in streams]

        if stream_type == STREAM2_TYPE_PROFILE:
            return list(Profile.objects.filter(pk__in=object_ids))
        elif stream_type == STREAM2_TYPE_TAG:
            return list(Tag.objects.filter(pk__in=object_ids))
        else:
            return listens


def listen_to_stream(listener, stream):
    """
    add a stream to user listening
    """
    try:
        Listen.objects.get(listener=listener, stream=stream)
    except Listen.DoesNotExist:
        listen = Listen(listener=listener, stream=stream)
        listen.save()


def remove_listener_from_stream(listener, stream):
    """
    remove a stream from user listening
    """
    listen = None
    try:
        listen = Listen.objects.get(listener=listener, stream=stream)
    except Listen.DoesNotExist:
        pass

    if listen:
        listen.delete()