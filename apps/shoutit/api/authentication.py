from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models.query_utils import Q
from django.views.decorators.csrf import csrf_exempt
from piston3 import oauth
from piston3.authentication import initialize_server_request, INVALID_PARAMS_RESPONSE, send_oauth_error
from apps.shoutit.controllers.gplus_controller import user_from_gplus_code
from apps.shoutit.controllers.facebook_controller import user_from_facebook_auth_response
from apps.shoutit.api.renderers import render_user
from apps.shoutit.utils import JsonResponse, JsonResponseBadRequest


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


def get_access_token(request, user):

    # step 1: fill request.user
    if not user:
        raise ObjectDoesNotExist("request.user should be filled with the logged in user")
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
        oauth_request.sign_request(oauth_server.signature_methods[oauth_request.get_parameter('oauth_signature_method')], request_token.consumer, request_token)
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
        'user': render_user(user, True, 3)
    }
    return JsonResponse(token)


@csrf_exempt
def get_gplus_access_token(request):

    # get or create shoutit user using the one time google code
    if not (hasattr(request, 'json_data') and 'code' in request.json_data and request.json_data['code']):
        return JsonResponseBadRequest({'error': "google one time code should be specified."})
    code = request.json_data['code']

    try:
        request.is_api = True
        error, user = user_from_gplus_code(request, code)
    except BaseException, e:
        return JsonResponseBadRequest({'error': e.message})

    if not user:
        return JsonResponseBadRequest({'error': error.message})

    return get_access_token(request, user)


@csrf_exempt
def get_facebook_access_token(request):

    # get or create shoutit user using the facebook auth response
    if not (hasattr(request, 'json_data') and 'auth_response' in request.json_data and request.json_data['auth_response']):
        return JsonResponseBadRequest({'error': "facebook auth response should be specified."})
    auth_response = request.json_data['auth_response']

    try:
        request.is_api = True
        error, user = user_from_facebook_auth_response(request, auth_response)
    except BaseException, e:
        return JsonResponseBadRequest({'error': e.message})

    if not user:
        return JsonResponseBadRequest({'error': error.message})

    return get_access_token(request, user)


#todo: not used
@csrf_exempt
def get_basic_access_token(request):

    # step 1: fill request.user
    if not 'credential' in request.REQUEST or not request.REQUEST['credential']:
        return HttpResponseBadRequest('username or email or mobile should be specified.')
    credential = request.REQUEST['credential']

    if not 'password' in request.REQUEST or not request.REQUEST['password']:
        return HttpResponseBadRequest('no password specified.')
    password = request.REQUEST['password']

    try:
        user = User.objects.get(Q(username__iexact=credential.strip()) | Q(email__iexact=credential.strip()) | Q(Profile__Mobile__iexact=credential.strip()))
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
        oauth_request.sign_request(oauth_server.signature_methods[oauth_request.get_parameter('oauth_signature_method')], request_token.consumer, request_token)
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
