from django.utils.translation import check_for_language
from apps.shoutit.controllers import shout_controller
from common.tagged_cache import TaggedCache
from apps.shoutit.utils import *
from apps.shoutit.constants import *

def get_shouts_PointId_inViewPort(downLeftLat, downLeftLng, upRightLat, upRightLng):
    if downLeftLng > upRightLng:
        right_shouts = shout_controller.GetLandingShouts(downLeftLat, -180.0, upRightLat, upRightLng)
        left_shouts = shout_controller.GetLandingShouts(downLeftLat, downLeftLng, upRightLat, 180.0)
        from itertools import chain

        shouts = list(chain(right_shouts, left_shouts))
    else:
        shouts = shout_controller.GetLandingShouts(downLeftLat, downLeftLng, upRightLat, upRightLng)
    return shouts, [[shout['Latitude'], shout['Longitude']] for shout in shouts]

def get_nearest_points_to_clusters(centroids, shoutPoints, shouts):
    nearestPoints = []
    nearestPointsIds = []
    nearestPointsTypes = []
    from numpy import argmin, sqrt, sum

    for clusterPos in centroids:
        diff = shoutPoints - clusterPos
        dist = sqrt(sum(diff ** 2, axis=-1))
        nearest_index = int(argmin(dist))

        nearestPoints.append(str(shoutPoints[nearest_index][0]) + ' ' + str(shoutPoints[nearest_index][1]))
        nearestPointsIds.append(IntToBase62(shouts[nearest_index]['id']))
        nearestPointsTypes.append(shouts[nearest_index]['Type'])
    return nearestPoints, nearestPointsIds, nearestPointsTypes


def set_request_language(request, lang_code):
    if lang_code and check_for_language(lang_code):
        if hasattr(request, 'session'):
            request.session['django_language'] = lang_code
        if request.user.is_authenticated():
            TaggedCache.set('perma|language|%d' % request.user.pk, lang_code, timeout=10 * 356 * 24 * 60 * 60)
        elif hasattr(request, 'session'):
            TaggedCache.set('perma|language|%s' % request.session.session_key, lang_code, timeout=10 * 356 * 24 * 60 * 60)
    else:
        TaggedCache.set('perma|language|%s' % request.session.session_key, settings.DEFAULT_LANGUAGE_CODE, timeout=10 * 356 * 24 * 60 * 60)
