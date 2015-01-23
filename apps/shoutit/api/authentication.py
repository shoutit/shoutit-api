from piston3 import oauth
from piston3.authentication import initialize_server_request, INVALID_PARAMS_RESPONSE, send_oauth_error

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models.query_utils import Q
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.shoutit.utils import JsonResponse, JsonResponseBadRequest
from apps.shoutit.models import User
from apps.shoutit.controllers.gplus_controller import user_from_gplus_code, unlink_gplus_user, link_gplus_user
from apps.shoutit.controllers.facebook_controller import user_from_facebook_auth_response, unlink_facebook_user, link_facebook_user
from apps.shoutit.api.renderers import render_user


@require_GET
def get_request_token(request):

    oauth_server, oauth_request = initialize_server_request(request)

    if oauth_server is None:
        return INVALID_PARAMS_RESPONSE

    try:
        request_token = oauth_server.fetch_request_token(oauth_request)
    except oauth.OAuthError as err:
        return send_oauth_error(err)

    token = {
        'oauth_token': request_token.key,
        'oauth_token_secret': request_token.secret
    }
    return JsonResponse(token)


@csrf_exempt
@require_POST
def get_access_token_using_social_channel(request, social_channel=None):

    # step 1: fill request.user
    try:
        if not (hasattr(request, 'json_data') and isinstance(request.json_data['social_channel_response'], dict)):
            raise KeyError("valid json object with social_channel_response")

        auth_data = request.json_data['social_channel_response']
        initial_user = 'user' in request.json_data and request.json_data['user'] or None
        request.is_api = True

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
                return JsonResponseBadRequest({'error': "missing " + k.message})

    except Exception, e:
        return JsonResponseBadRequest({'error': e.message})

    if not user:
        return JsonResponseBadRequest({'error': error.message})

    request.user = user

    # step 2: authorize the request token, do the verification on air
    oauth_server, oauth_request = initialize_server_request(request)

    if oauth_server is None or oauth_request is None:
        return INVALID_PARAMS_RESPONSE

    try:
        request_token = oauth_server.fetch_request_token(oauth_request)
    except oauth.OAuthError as err:
        return send_oauth_error(err)

    try:
        request_token = oauth_server.authorize_token(request_token, request.user)
        # after authorization we need to set the verifier and therefore new signature for oauth_request
        oauth_request.set_parameter('oauth_verifier', request_token.verifier)
        oauth_request.sign_request(oauth_server.signature_methods[oauth_request.get_parameter('oauth_signature_method')],
                                   request_token.consumer, request_token)
    except oauth.OAuthError as err:
        return send_oauth_error(err)

    # step 3: create access token for user
    try:
        access_token = oauth_server.fetch_access_token(oauth_request)
    except oauth.OAuthError as err:
        return send_oauth_error(err)

    token = {
        'access_token': access_token.key,
        'access_token_secret': access_token.secret,
        'user': render_user(user, level=4, owner=True)
    }
    return JsonResponse(token)


@csrf_exempt
def relink_social_channel(request, social_channel=None):

    if request.method == 'DELETE':
        if social_channel == 'gplus':
            if not hasattr(request.user, 'linked_facebook'):
                return JsonResponseBadRequest({'error': "at least one social account should be linked"})
            unlink_gplus_user(request)

        elif social_channel == 'facebook':
            if not hasattr(request.user, 'linked_gplus'):
                return JsonResponseBadRequest({'error': "at least one social account should be linked"})
            unlink_facebook_user(request)

    elif request.method == 'POST':

        try:
            if not (hasattr(request, 'json_data') and isinstance(request.json_data['social_channel_response'], dict)):
                raise KeyError("valid json object with social_channel_response")

            auth_data = request.json_data['social_channel_response']
            request.is_api = True

            if social_channel == 'gplus':
                if not ('code' in auth_data and auth_data['code']):
                    raise KeyError("valid google one time 'code'.")

                error, success = link_gplus_user(request, auth_data['code'])

            elif social_channel == 'facebook':
                if not ('accessToken' in auth_data and auth_data['accessToken']):
                    raise KeyError("valid facebook 'accessToken'")

                error, success = link_facebook_user(request, auth_data)

            else:
                error, success = Exception("unsupported social channel: " + social_channel), False

        except KeyError, k:
            return JsonResponseBadRequest({'error': "missing " + k.message})

        except Exception, e:
            return JsonResponseBadRequest({'error': e.message})

        if not success:
            return JsonResponseBadRequest({'error': error.message})

    return JsonResponse({
        'success': True,
        'message': "%s %slinked successfully" % (social_channel, 'un' if request.method == 'DELETE' else '')
    })


# todo: not used
@csrf_exempt
@require_POST
def get_basic_access_token(request):

    # step 1: fill request.user
    if 'credential' not in request.REQUEST or not request.REQUEST['credential']:
        return HttpResponseBadRequest('username or email or mobile should be specified.')
    credential = request.REQUEST['credential']

    if 'password' not in request.REQUEST or not request.REQUEST['password']:
        return HttpResponseBadRequest('no password specified.')
    password = request.REQUEST['password']

    try:
        user = User.objects.get(Q(username__iexact=credential.strip())
                                | Q(email__iexact=credential.strip()) | Q(Profile__Mobile__iexact=credential.strip()))
    except ObjectDoesNotExist:
        return HttpResponseBadRequest('Invalid username or password.')
    except MultipleObjectsReturned:
        return HttpResponseBadRequest('Invalid username or password.')

    if not user.check_password(password.strip()):
        return HttpResponseBadRequest('Invalid username or password.')

    request.user = user

    # step 2: authorize the request token, do the verification on air
    oauth_server, oauth_request = initialize_server_request(request)

    if oauth_server is None or oauth_request is None:
        return INVALID_PARAMS_RESPONSE

    try:
        request_token = oauth_server.fetch_request_token(oauth_request)
    except oauth.OAuthError as err:
        return send_oauth_error(err)

    try:
        request_token = oauth_server.authorize_token(request_token, request.user)
        # after authorization we need to set the verifier and therefore new signature for oauth_request
        oauth_request.set_parameter('oauth_verifier', request_token.verifier)
        oauth_request.sign_request(oauth_server.signature_methods[oauth_request.get_parameter('oauth_signature_method')],
                                   request_token.consumer, request_token)
    except oauth.OAuthError as err:
        return send_oauth_error(err)

    # step 3: create access token for user
    try:
        access_token = oauth_server.fetch_access_token(oauth_request)
    except oauth.OAuthError as err:
        return send_oauth_error(err)

    token = {
        'access_token': access_token.key,
        'access_token_secret': access_token.secret,
    }
    return JsonResponse(token)
