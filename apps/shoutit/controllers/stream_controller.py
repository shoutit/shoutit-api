from datetime import datetime, timedelta
import time
from django.db import connection
from django.db.models.expressions import F

from django.db.models.query_utils import Q
from apps.shoutit.constants import STREAM_TYPE_RELATED, STREAM_TYPE_RECOMMENDED, DEFAULT_PAGE_SIZE, PRICE_RANK_TYPE, POST_TYPE_EXPERIENCE, \
    POST_TYPE_BUY, POST_TYPE_SELL, FOLLOW_RANK_TYPE, DISTANCE_RANK_TYPE, TIME_RANK_TYPE, \
    STREAM2_TYPE_PROFILE, STREAM2_TYPE_TAG

from django.conf import settings
from apps.shoutit.models import Stream, ShoutWrap, Shout, Tag, StoredImage, Trade, Stream2, User, Listen, Profile
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


def MaxFollowings(ids, country_code, province_code, filters):
    shouts = Trade.objects.GetValidTrades(country_code=country_code, province_code=province_code).filter(**filters).select_related(
        'Streams').filter(Streams__pk__in=ids).values('StreamsCode')
    mutuals = [len(set(int(f) for f in shout['StreamsCode'].split(',') if len(shout['StreamsCode'].strip()) > 0) & set(ids)) for shout in
               shouts]
    return max(mutuals) if mutuals else 0


def MaxDistance(points, lat, long):
    max_distance = 180
    if len(points) > 0:
        codes = [[float(point['Latitude']), float(point['Longitude'])] for point in points]
        observation = [float(lat), float(long)]
        farest_index = utils.get_farest_point(observation, codes)
        farest_point = points[farest_index]
        max_distance = utils.normalized_distance(farest_point['Latitude'], farest_point['Longitude'], lat, long)

    return max_distance


def GetShoutTimeOrder(id, country_code, province_code, limit=0):
    shout_qs = Trade.objects.GetValidTrades(country_code=country_code, province_code=province_code).order_by('-DatePublished')
    shout_qs = shout_qs.values('id')
    shouts = list(shout_qs)
    shouts = [shout['id'] for shout in shouts]
    try:
        index = shouts.index(id)
        return index > DEFAULT_PAGE_SIZE and DEFAULT_PAGE_SIZE or index
    except ValueError, e:
        return 0


def GetRankedShoutsIDs(user, rank_type_flag, country_code='', province_code='', lat=0.0, long=0.0, start_index=None, end_index=None,
                       filter_types=[], filter_query=None, filter_tags=[]):
    # Selects shout IDs from database in the right order.
    #		---------------------------------------------------
    #		user: the User displaying shouts.
    #		rank_type_flag: determines the combination of the types of ranking you like to do.. (see constants.py).
    #		country_code, province_code: filtering criteria.
    #		lat, long: current location.
    #		start_index, end index: filtering criteria.
    #		filter_types: array of types you like to filter on(see constants.py for types).
    #		filter_query: a search string, work on shout item name and shout text.
    #		filter_tags: array of tags you like to filter on.
    #		RETURNS: array of tuple(shout id, shout rank).

    # initializing variables
    user_followings_ids = []
    if user is not None:
        #     user_followings_ids = [x['id'] for x in Stream.objects.filter(followship__follower=user.profile).values('id')]  # todo: check!
        user_followings_ids = [stream['id'] for stream in Stream2.objects.filter(listen__listener=user).values('id')]

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
            max_followings = MaxFollowings(user_followings_ids, country_code, province_code, filters)
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
        if lat is not None and long is not None:
            max_distance = MaxDistance(points, lat, long)
            if max_distance > 0.0:
                extra_order_bys += 'power( ' + str(settings.RANK_COEFFICIENT_DISTANCE) + \
                                   ' * (normalized_distance("shoutit_post"."Latitude", "shoutit_post"."Longitude", ' \
                                   'CAST(%f as DOUBLE PRECISION), CAST(%f as DOUBLE PRECISION)) / ' \
                                   'CAST(%.100f as DOUBLE PRECISION)' \
                                   '), 2.0) + ' % (float(lat), float(long), max_distance)
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
    query_string = unicode(shout_qs.values('id', 'rank', *additional_selects).query)
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
        if len(user_followings_ids):
            index = (query_string.find(qp) + len(qp))
            query_string = \
                unicode(query_string[:index]) + ' and "shoutit_post_Streams"."stream_id" IN (%s) ' % unicode(user_followings_ids)[
                                                                                                     1:-1] + unicode(query_string[index:])

    # executing query SQL & fetching shout IDs
    cursor = connection.cursor()
    cursor.execute(' '' ' + query_string + ' '' ')
    return [(row[1], row[0]) for row in cursor.fetchall() if row and len(row)]


def __GetStreamOfShoutsWithTags(rank_flag, user=None, lat=None, long=None, country_code='', province_code='', show_expired=False, *args,
                                **filters):
    if not country_code:
        country_code = ''
    if not province_code:
        province_code = ''

    end_index = None
    if 'end_index' in filters:
        end_index = filters['end_index']
        del filters['end_index']

    start_index = None
    if 'start_index' in filters:
        start_index = filters['start_index']
        del filters['start_index']

    today = datetime.today()
    days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
    begin = today - days

    base_timestamp = int(time.mktime(begin.utctimetuple()))
    now_timestamp = int(time.mktime(datetime.now().utctimetuple()))
    now_timestamp_string = str(datetime.now())

    extra_order_bys = ''
    rank_count = 0

    shout_qs = Trade.objects.GetValidTrades(country_code=country_code, province_code=province_code,
                                            get_expired=show_expired).select_related('Item', 'Item__Currency', 'OwnerUser',
                                                                                     'OwnerUser__Profile', 'Tags').filter(*args, **filters)

    # Calculating the Distance axis:
    if int(rank_flag & DISTANCE_RANK_TYPE):
        # A temproray solution for max distance:
        points = list(
            Trade.objects.GetValidTrades(country_code=country_code, province_code=province_code).filter(**filters).values('Latitude',
                                                                                                                          'Longitude'))
        if lat is not None and long is not None:
            max_distance = MaxDistance(points, lat, long)
            if max_distance > 0.0:
                extra_order_bys += '(normalized_distance("shoutit_post"."Latitude", "shoutit_post"."Longitude", CAST(%f as DOUBLE PRECISION), CAST(%f as DOUBLE PRECISION)) / CAST(%f as DOUBLE PRECISION)) + ' % (
                lat, long, max_distance)
                rank_count += 1

    # Calculating the Time axis:
    if int(rank_flag & TIME_RANK_TYPE):
        extra_order_bys += '(extract (epoch from age(\'%s\', "shoutit_post"."DatePublished"))/ %d) + ' % (
        now_timestamp_string, now_timestamp - base_timestamp)
        rank_count += 1

    # Calculating the Mutual Streams axis:
    if int(rank_flag & FOLLOW_RANK_TYPE):
        if user is not None:
            ids = [x['id'] for x in Stream.objects.filter(followship__follower__pk=user.profile.id).values('id')]
            max_followings = MaxFollowings(ids, country_code, province_code, filters)
            shout_qs = shout_qs.filter(Streams__pk__in=ids)
            #todo: find way to join tables
            _connection = (None, Shout.get_meta().db_table, ((None, None),))
            shout_qs.query.join(connection=_connection)
            shout_qs.query.get_initial_alias()
            _connection = (
                Shout._meta.db_table,
                Shout.Streams.field.m2m_db_table(),
                ((Shout._meta.pk.column, Shout.Streams.field.m2m_column_name()),)
            )
            shout_qs.query.join(connection=_connection, join_field=Shout.Streams, outer_if_first=True)
            if max_followings > 0:
                extra_order_bys += '(1 - (CAST(COUNT("shoutit_post_Streams"."stream_id") AS DOUBLE PRECISION) / CAST(%d AS DOUBLE PRECISION))) + ' % max_followings
                rank_count += 1

    if int(rank_flag & PRICE_RANK_TYPE):
        extra_order_bys += '("Price"/(SELECT MAX("Price") FROM "shoutit_item")) + '
        rank_count += 1

    if rank_count:
        extra_order_bys = extra_order_bys.strip()
        extra_order_bys = '(' + extra_order_bys[:-1] + ') / %d' % rank_count
    else:
        extra_order_bys = ''

    where_custom_clause = ['"shoutit_post"."DatePublished" BETWEEN \'%s\' and \'%s\'' % (str(begin), str(today))]
    if extra_order_bys != '':
        shout_qs = shout_qs.distinct().extra(select={'rank': extra_order_bys}).extra(order_by=['rank'])[start_index:end_index]
    else:
        shout_qs = shout_qs.distinct().order_by('-DatePublished')[start_index:end_index]

    #todo: find way to join tables
    #query_string = unicode(shout_qs.query)
    #qp = ' LEFT OUTER JOIN "shoutit_post_Streams" ON ("shoutit_shout"."post_ptr_id" = "shoutit_post_Streams"."post_id") '
    #if int(rank_flag & FOLLOW_RANK_TYPE):
    #    if user is not None:
    #        where_index = query_string.find('WHERE')
    #        query_string = unicode(query_string[:where_index]) + unicode(qp) + unicode(query_string[where_index:])
    #
    #executing query SQL & fetching shout IDs
    #cursor = connection.cursor()
    #cursor.execute(' '' ' + query_string + ' '' ')
    #shouts = list(cursor.fetchall())
    shouts = list(shout_qs)
    if shouts:
        tags = Tag.objects.select_related('Creator').prefetch_related('Shouts')
        tags = tags.extra(where=['shout_id IN (%s)' % ','.join([str(shout.pk) for shout in shouts])])
        #todo: find way to join tables
        tags_with_shout_id = list(tags.values('id', 'Name', 'Creator', 'Image', 'DateCreated', 'Definition', 'Shouts__id'))
        #tags = Tag.objects.select_related('Creator').extra(select={'shout_id' : '"%s"."%s"' % (Shout.Tags.field.m2m_db_table(), Shout.Tags.field.m2m_column_name())})
        #_connection = (None, Tag._meta.db_table, ((None, None),))
        #tags.query.join(connection=_connection)
        #_connection = (
        #    Tag._meta.db_table,
        #    Shout.Tags.field.m2m_db_table(),
        #    ((Tag._meta.pk.column, Shout.Tags.field.m2m_reverse_name()),)
        #)
        #tags.query.join(connection=_connection, outer_if_first=True)
        #tags_with_shout_id = list(tags)
    else:
        tags_with_shout_id = []
    images = StoredImage.objects.filter(
        Item__pk__in=[shout.Item.pk for shout in shouts if shout.Type == POST_TYPE_BUY or shout.Type == POST_TYPE_SELL]).order_by('Image').select_related('Item')

    for i in range(len(shouts)):
        shouts[i].SetTags([tag for tag in tags_with_shout_id if tag['Shouts__id'] == shouts[i].pk])
        tags_with_shout_id = [tag for tag in tags_with_shout_id if tag['Shouts__id'] != shouts[i].pk]
        #shouts[i].SetTags([tag for tag in tags_with_shout_id if tag.shout_id == shouts[i].pk])
        #tags_with_shout_id = [tag for tag in tags_with_shout_id if tag.shout_id != shouts[i].pk]

        shouts[i].Item.SetImages([image for image in images if image.Item_id == shouts[i].Item.pk])
        images = [image for image in images if image.Item_id != shouts[i].Item.pk]
    return shouts


def GetShoutRecommendedShoutStream(base_shout, type, start_index=None, end_index=None, exclude_shouter=True):
    filters = {}

    today = datetime.today()
    days = timedelta(days=int(settings.MAX_EXPIRY_DAYS))
    begin = today - days
    filters['Type'] = int(type)
    filters['Tags__pk__in'] = [t.id for t in base_shout.GetTags()]

    base_timestamp = int(time.mktime(begin.utctimetuple()))
    now_timestamp = int(time.mktime(datetime.now().utctimetuple()))
    now_timestamp_string = str(datetime.now())

    extra_order_bys = ''
    points = list(
        Trade.objects.GetValidTrades(country_code=base_shout.CountryCode, province_code=base_shout.ProvinceCode).filter(**filters).values(
            'Latitude', 'Longitude'))
    max_distance = MaxDistance(points, float(base_shout.Latitude), float(base_shout.Longitude))
    ids = [int(x) for x in base_shout.StreamsCode.split(',')]
    max_followings = MaxFollowings(ids, base_shout.CountryCode, base_shout.ProvinceCode, filters)
    max_price = 1.0

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
        'Item', 'Item__Currency', 'OwnerUser__Profile', 'Tags').filter(**filters).filter(~Q(pk=base_shout.id))
    if exclude_shouter:
        shout_qs = shout_qs.filter(~Q(OwnerUser=base_shout.OwnerUser))
    shout_qs = shout_qs.extra(select={'time_rank': '(extract (epoch from age(\'%s\', "shoutit_post"."DatePublished"))/ %d)' % (
    now_timestamp_string, now_timestamp - base_timestamp)})
    shout_qs = shout_qs.extra(select={'rank': extra_order_bys}).extra(order_by=['rank'])[start_index:end_index]
    shouts = list(shout_qs)
    if shouts:
        tags = Tag.objects.select_related('Creator').prefetch_related('Shouts')
        tags = tags.extra(where=['shout_id IN (%s)' % ','.join([str(shout.pk) for shout in shouts])])
        tags_with_shout_id = list(tags.values('id', 'Name', 'Creator', 'Image', 'DateCreated', 'Definition', 'Shouts__id'))
        # tags = Tag.objects.select_related('Creator').extra(select={'shout_id' : '"%s"."%s"' % (Shout.Tags.field.m2m_db_table(), Shout.Tags.field.m2m_column_name())})
        #_connection = (None, Tag._meta.db_table, ((None, None),))
        #tags.query.join(connection=_connection)
        #_connection = (
        #    Tag._meta.db_table,
        #    Shout.Tags.field.m2m_db_table(),
        #    ((Tag._meta.pk.column, Shout.Tags.field.m2m_reverse_name()),)
        #)
        #tags.query.join(connection=_connection, outer_if_first=True)
        #tags = tags.extra(where=['shout_id IN (%s)' % ','.join([str(shout.pk) for shout in shouts])])
        #tags_with_shout_id = list(tags)
    else:
        tags_with_shout_id = []
    images = StoredImage.objects.filter(Q(Shout__pk__in=[shout.pk for shout in shouts if shout.Type == POST_TYPE_EXPERIENCE]) | Q(
        Item__pk__in=[shout.Item.pk for shout in shouts if shout.Type != POST_TYPE_EXPERIENCE])).order_by('Image')

    for i in range(len(shouts)):
        shout = shouts[i]

        shout.rank = ((shout.rank ** 2) * rank_count - shout.time_rank) / (rank_count - 1)

        shouts[i].SetTags([tag for tag in tags_with_shout_id if tag['Shouts__id'] == shouts[i].pk])
        tags_with_shout_id = [tag for tag in tags_with_shout_id if tag['Shouts__id'] != shouts[i].pk]
        # shouts[i].SetTags([tag for tag in tags_with_shout_id if tag.shout_id == shouts[i].pk])
        #tags_with_shout_id = [tag for tag in tags_with_shout_id if tag.shout_id != shouts[i].pk]

        shouts[i].Item.SetImages([image for image in images if image.Item_id == shouts[i].Item.pk])
        images = [image for image in images if image.Item_id != shouts[i].Item.pk]
    return shouts


def GetTradesByIDs(ids):
    # Select shouts from database according to their IDs, including other objects related to every shout.
    #		ids: array of shout IDs
    #		RETURNS: array of shout objects

    if ids is None or len(ids) == 0:
        return []
    #todo: choose which statement with less queries and enough data
    #todo: find way to join tables
    #shout_qs = Trade.objects.GetValidTrades().select_related('Item', 'Item__Currency', 'OwnerUser', 'OwnerUser__Profile').prefetch_related('Tags','Item__Images').filter(pk__in = ids)
    #shout_qs = Trade.objects.GetValidTrades().select_related('Item', 'Item__Currency', 'OwnerUser', 'OwnerUser__Profile','Tags').filter(pk__in = ids)
    shout_qs = Trade.objects.GetValidTrades().select_related('Item', 'Item__Currency', 'OwnerUser', 'OwnerUser__Profile').filter(pk__in=ids)
    shouts = list(shout_qs)
    #if shouts:
    #    tags = Tag.objects.select_related('Creator').extra(select={'shout_id' : '"%s"."%s"' % (Trade.Tags.field.m2m_db_table(), Trade.Tags.field.m2m_column_name())})
    #    _connection = (None, Tag._meta.db_table, ((None, None),))
    #    tags.query.join(connection=_connection)
    #    _connection = (
    #        Tag._meta.db_table,
    #        Trade.Tags.field.m2m_db_table(),
    #        ((Tag._meta.pk.column, Trade.Tags.field.m2m_reverse_name()),)
    #    )
    #    tags.query.join(connection=_connection, join_field=Trade.Tags.field, outer_if_first=True)
    #    tags = tags.extra(where=['shout_id IN (%s)' % ','.join([str(shout.pk) for shout in shouts])])
    #    tags_with_shout_id = list(tags)
    #else:
    #    tags_with_shout_id = []
    #images = StoredImage.objects.filter(Item__pk__in = [shout.Item.pk for shout in shouts if shout.Type == POST_TYPE_BUY or shout.Type == POST_TYPE_SELL]).order_by('Image').select_related('Item')

    #for i in range(len(shouts)):
    #    shout = shouts[i]

    #shouts[i].SetTags([tag for tag in tags_with_shout_id if tag.shout_id == shouts[i].pk])
    #tags_with_shout_id = [tag for tag in tags_with_shout_id if tag.shout_id != shouts[i].pk]

    #if shouts[i].Type <> int(POST_TYPE_EXPERIENCE):
    #    shouts[i].Item.SetImages([image for image in images if image.Item_id == shouts[i].Item.pk])
    #    images = [image for image in images if image.Item_id != shouts[i].Item.pk]
    #		else:
    #			shouts[i].SetImages([image for image in images if image.Shout_id == shouts[i].pk])
    #			images = [image for image in images if image.Shout_id != shouts[i].pk]

    return shouts


def GetStreamShouts(stream, start_index=None, end_index=None, show_expired=False, country='', province=''):
    return __GetStreamOfShoutsWithTags(TIME_RANK_TYPE, user=None, lat=None, long=None, country_code=country, province_code=province,
                                       IsMuted__exact=False, Streams__pk__in=[stream.pk], start_index=start_index, end_index=end_index,
                                       show_expired=show_expired)


def GetRankedStreamShouts(stream):
    if stream:
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
    else:
        return []


# todo: reduce queries by supplying the trade objects with necessary tags, images, etc
# todo: use country, city, etc
def get_stream_shouts(stream, start_index=0, end_index=DEFAULT_PAGE_SIZE, show_expired=False, country=None, city=None):
    post_ids = [post['id'] for post in stream.Posts.filter(Type__in=[POST_TYPE_BUY, POST_TYPE_SELL]).values('id')[start_index:end_index]]
    trades = Trade.objects.filter(pk__in=post_ids)
    return trades


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
        stream_ids = [listen.stream_id for listen in listens]
        streams = Stream2.objects.filter(id__in=stream_ids)
        object_ids = [stream.object_id for stream in streams]

        if stream_type == STREAM2_TYPE_PROFILE:
            return list(Profile.objects.filter(id__in=object_ids))
        elif stream_type == STREAM2_TYPE_TAG:
            return list(Tag.objects.filter(id__in=object_ids))
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