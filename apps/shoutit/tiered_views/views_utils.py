from django.conf import settings
from django.utils.translation import check_for_language
from common.tagged_cache import TaggedCache


def set_request_language(request, lang_code):
    if lang_code and check_for_language(lang_code):
        if hasattr(request, 'session'):
            request.session['django_language'] = lang_code
        if request.user.is_authenticated():
            TaggedCache.set('perma|language|%s' % request.user.pk, lang_code, timeout=10 * 356 * 24 * 60 * 60)
        elif hasattr(request, 'session'):
            TaggedCache.set('perma|language|%s' % request.session.session_key, lang_code, timeout=10 * 356 * 24 * 60 * 60)
    else:
        TaggedCache.set('perma|language|%s' % request.session.session_key, settings.DEFAULT_LANGUAGE_CODE, timeout=10 * 356 * 24 * 60 * 60)
