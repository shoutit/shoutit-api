from __future__ import print_function
from six import string_types

import django
from django.http import HttpResponse
from django import get_version as django_version
from django.utils.crypto import get_random_string


__version__ = '0.2.3rc1'


def get_version():
    return __version__


def format_error(error):
    return u"Piston/%s (Django %s) crash report:\n\n%s" % \
           (get_version(), django_version(), error)


class RCFactory(object):
    """
    Status codes.
    """
    CODES = dict(ALL_OK=('OK', 200),
                 CREATED=('Created', 201),
                 ACCEPTED=('Accepted', 202),
                 DELETED=('', 204),  # 204 says "Don't send a body!"
                 BAD_REQUEST=('Bad Request', 400),
                 FORBIDDEN=('Forbidden', 401),
                 NOT_FOUND=('Not Found', 404),
                 NOT_ACCEPTABLE=('Not acceptable', 406),
                 DUPLICATE_ENTRY=('Conflict/Duplicate', 409),
                 NOT_HERE=('Gone', 410),
                 INTERNAL_ERROR=('Internal Error', 500),
                 NOT_IMPLEMENTED=('Not Implemented', 501),
                 THROTTLED=('Throttled', 503))

    def __getattr__(self, attr):
        """
        Returns a fresh `HttpResponse` when getting 
        an "attribute". This is backwards compatible
        with 0.2, which is important.
        """
        try:
            (r, c) = self.CODES.get(attr)
        except TypeError:
            raise AttributeError(attr)

        if django.VERSION < (1, 5):
            class HttpResponseWrapper(HttpResponse):
                """
                Wrap HttpResponse and make sure that the internal
                _is_string/_base_content_is_iter flag is updated when the
                _set_content method (via the content property) is called
                """

                def _set_content(self, content):
                    """
                    Set the _container and _is_string /
                    _base_content_is_iter properties based on the type of
                    the value parameter. This logic is in the construtor
                    for HttpResponse, but doesn't get repeated when
                    setting HttpResponse.content although this bug report
                    (feature request) suggests that it should:
                    http://code.djangoproject.com/ticket/9403
                    """
                    is_string = False
                    if not isinstance(content, string_types) and hasattr(content, '__iter__'):
                        self._container = content
                    else:
                        self._container = [content]
                        is_string = True
                    if django.VERSION >= (1, 4):
                        self._base_content_is_iter = not is_string
                    else:
                        self._is_string = is_string

                content = property(HttpResponse._get_content, _set_content)
        else:
            HttpResponseWrapper = HttpResponse

        return HttpResponseWrapper(r, content_type='text/plain', status=c)


rc = RCFactory()


def coerce_put_post(request):
    """
    Django doesn't particularly understand REST.
    In case we send data over PUT, Django won't
    actually look at the data and load it. We need
    to twist its arm here.
    
    The try/except abominiation here is due to a bug
    in mod_python. This should fix it.
    """
    if request.method == "PUT":
        # Bug fix: if _load_post_and_files has already been called, for
        # example by middleware accessing request.POST, the below code to
        # pretend the request is a POST instead of a PUT will be too late
        # to make a difference. Also calling _load_post_and_files will result 
        # in the following exception:
        # AttributeError: You cannot set the upload handlers after the upload has been processed.
        # The fix is to check for the presence of the _post field which is set 
        # the first time _load_post_and_files is called (both by wsgi.py and 
        # modpython.py). If it's set, the request has to be 'reset' to redo
        # the query value parsing in POST mode.
        if hasattr(request, '_post'):
            del request._post
            del request._files

        try:
            request.method = "POST"
            request._load_post_and_files()
            request.method = "PUT"
        except AttributeError:
            request.META['REQUEST_METHOD'] = 'POST'
            request._load_post_and_files()
            request.META['REQUEST_METHOD'] = 'PUT'

        request.PUT = request.POST


def generate_random(length):
    return get_random_string(length, "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789")
