import datetime
import time

import os
import re
from django import template
from django.template.base import VariableDoesNotExist
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse, NoReverseMatch
from widget_tweaks.templatetags.widget_tweaks import _process_field_attributes
from django.conf import settings

from shoutit.utils import shout_link as _shout_link, get_size_url, get_https_cdn, to_seo_friendly


register = template.Library()


@register.filter
def key(d, key_name):
    return d[key_name]


@register.filter
def mod(d, mod):
    return d % mod


@register.filter
def ca(a, b):
    return a + b


@register.simple_tag
def active(request, pattern, ext=''):
    if re.search(pattern + ext, request.path):
        return 'active'
    return ''


@register.filter
def rangeToIndex(value, index):
    try:
        if len(value) < index:
            return value
        else:
            return "%s %s" % (value[:index], '...')
    except IndexError:
        return value


@register.filter
def replacebr(v):
    return v.replace('<br />', '\n').replace('<br>', '\n').replace('<p></p>', '\n')


@register.filter
def thumbnail(url, size):
    return get_size_url(url, size)


cdn_re = re.compile(r'http://(([\w-]+)\.)+rackcdn\.(.*)')


@register.filter
def secure_url(url):
    if not settings.IS_SITE_SECURE:
        return url
    if not url.startswith('https'):
        if url.startswith('/'):
            url = settings.SITE_LINK + url
        if cdn_re.match(url):
            return get_https_cdn(url)
        url = url.replace('http://', 'https://')
    return url


@register.filter
def ISO8601(dt):
    formatted = time.strftime('%Y-%m-%dT%H:%M:%S', dt.timetuple())
    tz = str.format('{0:+06.2f}', -float(time.timezone) / 3600).replace('.', ':')
    return formatted + tz


@register.filter
def price(price, currency):
    result = '%.2f' % price if price - int(price) != 0 else '%d' % int(price)
    fpindex = result.find('.')
    csinteger_result = ''
    if fpindex != -1:
        integer_result = result[:fpindex]
        float_result = result[fpindex + 1:]
    else:
        integer_result = result

    regex = re.compile(r'^(\d+)(\d{3})$')
    m = regex.match(integer_result)

    if m:
        csinteger_result = m.group(2)
        integer_result = m.group(1)
        m = regex.match(integer_result)
        while m:
            csinteger_result = m.group(2) + ',' + csinteger_result
            integer_result = m.group(1)
            m = regex.match(integer_result)
    else:
        csinteger_result = integer_result
        integer_result = ''

    if integer_result:
        csinteger_result = integer_result + ',' + csinteger_result

    if fpindex != -1:
        result = csinteger_result + '.' + float_result
    else:
        result = csinteger_result
    return result + ' ' + currency


@register.filter
def date2ago(date_time):
    current_datetime = datetime.datetime.now()
    delta = str(current_datetime - date_time)
    if delta.find(',') > 0:
        days, hours = delta.split(',')
        days = int(days.split()[0].strip())
        hours, minutes = hours.split(':')[0:2]
    else:
        hours, minutes = delta.split(':')[0:2]
        days = 0
    days, hours, minutes = int(days), int(hours), int(minutes)
    datelets = []
    years, months, xdays = None, None, None
    plural = lambda x: 's' if x != 1 else ''
    if days >= 365:
        years = int(days / 365)
        datelets.append('%d year%s' % (years, plural(years)))
        days = days % 365
    if days >= 30 and days < 365:
        months = int(days / 30)
        datelets.append('%d month%s' % (months, plural(months)))
        days = days % 30
    if not years and days > 0 and days < 30:
        xdays = days
        datelets.append('%d day%s' % (xdays, plural(xdays)))
    if not (months or years) and hours != 0:
        datelets.append('%d hour%s' % (hours, plural(hours)))
    if not (xdays or months or years):
        datelets.append('%d minute%s' % (minutes, plural(minutes)))
    return ', '.join(datelets) + ' ago.'


# using the jquery template tags in side django templates
class VerbatimNode(template.Node):
    def __init__(self, text):
        self.text = text

    def render(self, context):
        return self.text


@register.tag
def verbatim(parser, token):
    text = []
    while 1:
        token = parser.tokens.pop(0)
        if token.contents == 'endverbatim':
            break
        if token.token_type == template.TOKEN_VAR:
            text.append('{{')
        elif token.token_type == template.TOKEN_BLOCK:
            text.append('{%')
        text.append(token.contents)
        if token.token_type == template.TOKEN_VAR:
            text.append('}}')
        elif token.token_type == template.TOKEN_BLOCK:
            text.append('%}')
    return VerbatimNode(''.join(text))


class CsrfTokenValueNode(template.Node):
    def render(self, context):
        csrf_token = context.get('csrf_token', None)
        if csrf_token:
            return mark_safe(csrf_token)


@register.tag
def csrf_token_value(parser, token):
    return CsrfTokenValueNode()


@register.tag(name="switch")
def do_switch(parser, token):
    """
    The ``{% switch %}`` tag compares a variable against one or more values in
    ``{% case %}`` tags, and outputs the contents of the matching block.  An
    optional ``{% else %}`` tag sets off the default output if no matches
    could be found::

        {% switch result_count %}
            {% case 0 %}
                There are no search results.
            {% case 1 %}
                There is one search result.
            {% else %}
                Jackpot! Your search found {{ result_count }} results.
        {% endswitch %}

    Each ``{% case %}`` tag can take multiple values to compare the variable
    against::

        {% switch username %}
            {% case "Jim" "Bob" "Joe" %}
                Me old mate {{ username }}! How ya doin?
            {% else %}
                Hello {{ username }}
        {% endswitch %}
    """
    bits = token.contents.split()
    tag_name = bits[0]
    if len(bits) != 2:
        raise template.TemplateSyntaxError("'%s' tag requires one argument" % tag_name)
    variable = parser.compile_filter(bits[1])

    class BlockTagList(object):
        # This is a bit of a hack, as it embeds knowledge of the behaviour
        # of Parser.parse() relating to the "parse_until" argument.
        def __init__(self, *names):
            self.names = set(names)

        def __contains__(self, token_contents):
            name = token_contents.split()[0]
            return name in self.names

    # Skip over everything before the first {% case %} tag
    parser.parse(BlockTagList('case', 'endswitch'))

    cases = []
    token = parser.next_token()
    got_case = False
    got_else = False
    while token.contents != 'endswitch':
        nodelist = parser.parse(BlockTagList('case', 'else', 'endswitch'))

        if got_else:
            raise template.TemplateSyntaxError("'else' must be last tag in '%s'." % tag_name)

        contents = token.contents.split()
        token_name, token_args = contents[0], contents[1:]

        if token_name == 'case':
            tests = map(parser.compile_filter, token_args)
            case = (tests, nodelist)
            got_case = True
        else:
            # The {% else %} tag
            case = (None, nodelist)
            got_else = True
        cases.append(case)
        token = parser.next_token()

    if not got_case:
        raise template.TemplateSyntaxError("'%s' must have at least one 'case'." % tag_name)

    return SwitchNode(variable, cases)


class SwitchNode(template.Node):
    def __init__(self, variable, cases):
        self.variable = variable
        self.cases = cases

    def __repr__(self):
        return "<Switch node>"

    def __iter__(self):
        for tests, nodelist in self.cases:
            for node in nodelist:
                yield node

    def get_nodes_by_type(self, nodetype):
        nodes = []
        if isinstance(self, nodetype):
            nodes.append(self)
        for tests, nodelist in self.cases:
            nodes.extend(nodelist.get_nodes_by_type(nodetype))
        return nodes

    def render(self, context):
        try:
            value_missing = False
            value = self.variable.resolve(context, True)
        except VariableDoesNotExist:
            no_value = True
            value_missing = None

        for tests, nodelist in self.cases:
            if tests is None:
                return nodelist.render(context)
            elif not value_missing:
                for test in tests:
                    test_value = test.resolve(context, True)
                    if value == test_value:
                        return nodelist.render(context)
        else:
            return ""


class SetVarNode(template.Node):
    def __init__(self, var_name, var_value):
        self.var_name = var_name
        self.var_value = var_value

    def render(self, context):
        try:
            value = template.Variable(self.var_value).resolve(context)
        except template.VariableDoesNotExist:
            value = ""
        context[self.var_name] = value
        return u""


class IncrementVarNode(template.Node):
    def __init__(self, var_name, var_value):
        self.var_name = var_name
        self.var_value = var_value

    def render(self, context):
        try:
            value = template.Variable(self.var_value).resolve(context)
        except template.VariableDoesNotExist:
            value = ""
        context[self.var_name] += value
        return u""


@register.tag(name="set")
def set_var(parser, token):
    """
    {% set <var_name> = <var_value> %}
    """
    parts = token.split_contents()
    if len(parts) < 4:
        raise template.TemplateSyntaxError("'set' tag must be of the form:  {% set <var_name>  = <var_value> %}")
    return SetVarNode(parts[1], parts[3])


@register.tag(name="incr")
def incr_var(parser, token):
    """
    {% incr <var_name> <incr_value> %}
    """
    parts = token.split_contents()
    if len(parts) < 3:
        raise template.TemplateSyntaxError("'incr' tag must be of the form:  {% incr <var_name> <incr_value> %}")
    return IncrementVarNode(parts[1], parts[2])


@register.filter('trans_attr')
def set_trans_attr(field, attr):
    text = attr.split(':', 1)[1]
    from shoutit.templatetags import translating_variables as tv

    if not text in tv.translated:
        tvf = open(os.path.join(os.path.dirname(__file__), 'translating_variables.py'), 'r')
        lines = [line for line in tvf]
        before = lines[:2]
        line = lines[2]
        after = lines[3:]
        tvf.close()
        tvf = open(os.path.join(os.path.dirname(__file__), 'translating_variables.py'), 'w')
        tvf.write(''.join(before))
        tvf.write('%s, "%s"]\n' % (line.strip()[:-1], text.replace('"', '\\"')))
        tvf.write(''.join(after))
        tvf.write('\nvar = _("%s")' % text.replace('"', '\\"'))
        tvf.close()
    attr = attr.split(':', 1)[0] + ':' + _(text)

    def process(widget, attrs, attribute, value):
        attrs[attribute] = value

    return _process_field_attributes(field, attr, process)


@register.simple_tag
def name2url(name):
    return to_seo_friendly(name)


@register.simple_tag
def shout_link(post):
    return _shout_link(post)


@register.simple_tag
def auth_login(request):
    """
    Include a login snippet if REST framework's login view is in the URLconf.
    """
    try:
        login_url = reverse('rest_framework:login')
    except NoReverseMatch:
        return ''

    snippet = "<a id='_user' href='{href}?next={next}'>Log in</a>".format(href=login_url, next=escape(request.path))
    return snippet


@register.simple_tag
def auth_logout(request, user):
    """
    Include a logout snippet if REST framework's logout view is in the URLconf.
    """
    try:
        logout_url = reverse('rest_framework:logout')
    except NoReverseMatch:
        return '<a id="_user">{user}</a>'.format(user=user)

    snippet = '<a id="_user" href="{href}?next={next}" title="Log out">{user}</a>'

    return snippet.format(user=user, href=logout_url, next=escape(request.path))
