from django.db import connection
from django.template import Template, Context
from django.conf import settings
import logging


class SQLLogToConsoleMiddleware(object):
    logger = logging.getLogger('SqlLogMiddleware')
    console_logger = logging.getLogger('SqlLogMiddleware_console')

    def process_response(self, request, response):
        self.print_queries(request)
        return response

    def print_queries(self, request=None):
        if settings.DEBUG and connection.queries:
            time = sum([float(q['time']) for q in connection.queries])
            t = Template(
                "*************\n{{url}}\n{{count}} quer{{count|pluralize:\"y,ies\"}} in {{time}} seconds:\n{% for sql in sqllog %}[{{forloop.counter}}] {{sql.time}}s: {{sql.sql|safe}}{% if not forloop.last %}\n\n{% endif %}{% endfor %}\n*************")
            self.logger.info(t.render(Context({'sqllog': connection.queries, 'count': len(connection.queries), 'time': time,
                                               'url': request and request.get_full_path() or ''})))
            try:
                self.console_logger.info(t.render(Context({'sqllog': connection.queries, 'count': len(connection.queries), 'time': time,
                                                           'url': request and request.get_full_path() or ''})))
            except UnicodeError:
                pass