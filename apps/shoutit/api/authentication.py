from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models.query_utils import Q
from django.http import HttpResponseBadRequest, HttpResponse
import json
from piston3 import oauth
from django.views.decorators.csrf import csrf_exempt
from piston3.authentication import initialize_server_request, INVALID_PARAMS_RESPONSE, send_oauth_error
from apps.shoutit.models import LinkedFacebookAccount
from apps.shoutit.controllers.gplus_controller import user_from_gplus_code
from apps.shoutit.api.renderers import render_user

@csrf_exempt
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
        'oauth_token_secret': request_token.secret,
    }
    return HttpResponse(json.dumps(token), content_type='application/json')


@csrf_exempt
def get_access_token(request):

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
    return HttpResponse(json.dumps(token), content_type='application/json')

@csrf_exempt
def get_gplus_access_token(request):

    # step 1: fill request.user
    if not 'code' in request.REQUEST or not request.REQUEST['code']:
        return HttpResponseBadRequest('google one time code should be specified.')
    code = request.REQUEST['code']

    try:
        request.is_api = True
        error, user = user_from_gplus_code(request, code)
    except BaseException, e:
        return HttpResponseBadRequest(json.dumps({'error': e.message}), content_type='application/json')

    if not user:
        return HttpResponseBadRequest(json.dumps({'error': error.message}), content_type='application/json')

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
        'user': render_user(user)
    }
    return HttpResponse(json.dumps(token), content_type='application/json')


@csrf_exempt
def get_facebook_token(request):
    oauth_request = get_oauth_request(request)

    if 'oauth_token' not in oauth_request:
        return HttpResponseBadRequest('No request token specified.')
    try:
        request_token = store.get_request_token(request, oauth_request, oauth_request['oauth_token'])
    except InvalidTokenError:
        return HttpResponseBadRequest('Invalid request token.')

    consumer = store.get_consumer_for_request_token(request, oauth_request, request_token)

    if not 'access_token' in request.REQUEST:
        return HttpResponseBadRequest('Invalid access token.')

    try:
        linked_account = LinkedFacebookAccount.objects.get(AccessToken=request.REQUEST['access_token'])
        user = linked_account.User
    except ObjectDoesNotExist:
        return HttpResponseBadRequest('Invalid access token.')

    request.user = user
    request_token = store.authorize_request_token(request, oauth_request, request_token)
    access_token = store.create_access_token(request, oauth_request, consumer, request_token)

    token = {
        'access_token': access_token.key,
        'access_token_secret': access_token.secret,
    }
    return HttpResponse(json.dumps(token), content_type='application/json')