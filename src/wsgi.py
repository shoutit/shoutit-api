"""
WSGI config for shout project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
import sys
from django.core.wsgi import get_wsgi_application  # NOQA

# Include src dir in sys.path a.k.a PYTHONPATH to be able to be able to import apps normally.
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shoutit.settings")
application = get_wsgi_application()
