import urlparse
import json

from django.conf import settings
from django.http import QueryDict, HttpResponse
from django.utils.decorators import available_attrs
from django.utils.functional import wraps
from django.utils.translation import ugettext as _

from common.constants import *


class XHRResult(object):
    code = ENUM_XHR_RESULT.SUCCESS
    message = ''
    message_type = ''
    form_errors = {}
    data = []

    def __init__(self, code=ENUM_XHR_RESULT.SUCCESS, message='', form_errors={}, data={}, message_type='success'):
        self.code = code
        self.message = message
        self.form_errors = form_errors
        self.data = data
        self.message_type = message_type

        self.response = {
            "code": code, "message": unicode(message), "errors": form_errors, "data": data,
            "message_type": self.message_type
        }

        self.json = json.dumps(self.response)

    def __str__(self):
        return self.json

    def __unicode__(self):
        return self.json


def xhr_respond(code, message, errors={}, data={}, message_type='success'):
    return HttpResponse(content=XHRResult(code, message, errors, data, message_type=message_type),
                        content_type='application/json')


def xhr_login_required(function=None):
    @wraps(function, assigned=available_attrs(function))
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated():
            return function(request, *args, **kwargs)
        else:
            if 'HTTP_REFERER' in request.META:
                referer_parts = urlparse.urlparse(request.META['HTTP_REFERER'])
                path = referer_parts[2]
                if referer_parts[3]:
                    path += ';' + referer_parts[3]
                if referer_parts[4]:
                    path += '?' + referer_parts[4]
                if referer_parts[5]:
                    path += '#' + referer_parts[5]
            else:
                path = '/'
            login_url_parts = list(urlparse.urlparse(settings.LOGIN_URL))
            querystring = QueryDict(login_url_parts[4], mutable=True)
            querystring['next'] = path
            login_url_parts[4] = querystring.urlencode(safe='/')
            return xhr_respond(ENUM_XHR_RESULT.REDIRECT, _("You are not signed in."),
                               data={'link': urlparse.urlunparse(login_url_parts)}, message_type='error')

    return wrapper


def redirect_to_modal_xhr(request,to, message, modal_key = None):
    if 'HTTP_REFERER' in request.META:
        referer_parts = urlparse.urlparse(request.META['HTTP_REFERER'])
        path = referer_parts[2]
        if referer_parts[3]:
            path += ';' + referer_parts[3]
        if referer_parts[4]:
            path += '?' + referer_parts[4]
        if referer_parts[5]:
            path += '#' + referer_parts[5]
    else:
        path = '/'
    _url_parts = list(urlparse.urlparse(to))
    querystring = QueryDict(_url_parts[4], mutable=True)
    querystring['next'] = path
    _url_parts[4] = querystring.urlencode(safe='/')
    post_data = {'link': urlparse.urlunparse(_url_parts)}
    if modal_key:
        post_data['modal_key'] = modal_key
    return xhr_respond(ENUM_XHR_RESULT.REDIRECT, message,
                       data=post_data, message_type='error')

#def redirect_to_login_xhr(request):
#	if 'HTTP_REFERER' in request.META:
#		referer_parts = urlparse.urlparse(request.META['HTTP_REFERER'])
#		path = referer_parts[2]
#		if referer_parts[3]:
#			path += ';' + referer_parts[3]
#		if referer_parts[4]:
#			path += '?' + referer_parts[4]
#		if referer_parts[5]:
#			path += '#' + referer_parts[5]
#	else:
#		path = '/'
#	login_url_parts = list(urlparse.urlparse(settings.LOGIN_URL))
#	querystring = QueryDict(login_url_parts[4], mutable=True)
#	querystring['next'] = path
#	login_url_parts[4] = querystring.urlencode(safe='/')
#	return xhr_respond(ENUM_XHR_RESULT.REDIRECT, "You are not signed in.",
#					   data={'link': urlparse.urlunparse(login_url_parts)}, message_type='error')
#
#def redirect_to_activate_xhr(request):
#	if 'HTTP_REFERER' in request.META:
#		referer_parts = urlparse.urlparse(request.META['HTTP_REFERER'])
#		path = referer_parts[2]
#		if referer_parts[3]:
#			path += ';' + referer_parts[3]
#		if referer_parts[4]:
#			path += '?' + referer_parts[4]
#		if referer_parts[5]:
#			path += '#' + referer_parts[5]
#	else:
#		path = '/'
#	activate_url_parts = list(urlparse.urlparse(settings.ACTIVATE_URL))
#	querystring = QueryDict(activate_url_parts[4], mutable=True)
#	querystring['next'] = path
#	activate_url_parts[4] = querystring.urlencode(safe='/')
#	return xhr_respond(ENUM_XHR_RESULT.REDIRECT, "You're not activated.",
#					   data={'link': urlparse.urlunparse(activate_url_parts)}, message_type='error')