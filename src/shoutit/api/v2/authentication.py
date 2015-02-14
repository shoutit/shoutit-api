# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.response import Response
from shoutit.api.renderers import render_user
from shoutit.controllers.facebook_controller import user_from_facebook_auth_response
from shoutit.controllers.gplus_controller import user_from_gplus_code


@csrf_exempt
@require_POST
def get_access_token_using_social_channel(request, social_channel=None):

    # step 1: fill request.user
    try:
        if not (hasattr(request, 'json_data') and isinstance(request.json_data['social_channel_response'], dict)):
            raise KeyError("valid json object with social_channel_response")

        auth_data = request.json_data['social_channel_response']
        initial_user = 'user' in request.json_data and request.json_data['user'] or None

        if social_channel == 'gplus':
            # get or create shoutit user using the one time google plus code
            if not ('code' in auth_data and auth_data['code']):
                raise KeyError("valid google one time 'code'.")

            error, user = user_from_gplus_code(request, auth_data['code'], initial_user)

        elif social_channel == 'facebook':
            # get or create shoutit user using the facebook auth response
            if not ('accessToken' in auth_data and auth_data['accessToken']):
                raise KeyError("valid facebook 'accessToken'")

            error, user = user_from_facebook_auth_response(request, auth_data, initial_user)

        else:
            error, user = Exception("unsupported social channel: " + social_channel), None

    except KeyError, k:
                return Response({'error': "missing " + str(k)})

    except Exception, e:
        return Response({'error': str(e)})

    if not user:
        return Response({'error': str(error)})

    request.user = user

    res = {
        'user': render_user(user, level=4, owner=True),
        'token': user.auth_token.key,
    }
    return Response(res)
