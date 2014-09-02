from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models.query_utils import Q
from django.http import HttpResponseBadRequest, HttpResponse
from urllib import urlencode
import json
from django.views.decorators.csrf import csrf_exempt
from piston3.authentication.oauth.store import store, InvalidConsumerError, InvalidTokenError
from piston3.authentication.oauth.utils import verify_oauth_request, get_oauth_request, require_params
from apps.shoutit.models import LinkedFacebookAccount


@csrf_exempt
def get_request_token(request):
    oauth_request = get_oauth_request(request)
    missing_params = require_params(oauth_request)
    if missing_params is not None:
        return missing_params
    try:
        consumer = store.get_consumer(request, oauth_request, oauth_request['oauth_consumer_key'])
    except InvalidConsumerError:
        return HttpResponseBadRequest('Invalid Consumer.')

    if not verify_oauth_request(request, oauth_request, consumer):
        return HttpResponseBadRequest('Could not verify OAuth request.')

    request_token = store.create_request_token(request, oauth_request, consumer, 'oob')

    token = {
        'oauth_token': request_token.key,
        'oauth_token_secret': request_token.secret,
    }
    return HttpResponse(json.dumps(token), content_type='application/json')


@csrf_exempt
def get_access_token(request):
    oauth_request = get_oauth_request(request)

    if 'oauth_token' not in oauth_request:
        return HttpResponseBadRequest('No request token specified.')

    try:
        request_token = store.get_request_token(request, oauth_request, oauth_request['oauth_token'])
    except InvalidTokenError:
        return HttpResponseBadRequest('Invalid request token.')

    consumer = store.get_consumer_for_request_token(request, oauth_request, request_token)

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
    request_token = store.authorize_request_token(request, oauth_request, request_token)
    access_token = store.create_access_token(request, oauth_request, consumer, request_token)

    token = {
        'access_token': access_token.key,
        'access_token_secret': access_token.secret,
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