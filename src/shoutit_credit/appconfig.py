from __future__ import unicode_literals
from django.apps import AppConfig
from django.db import ProgrammingError

from shoutit.utils import debug_logger


class ShoutitCreditConfig(AppConfig):
    name = 'shoutit_credit'
    label = 'shoutit_credit'
    verbose_name = "Shoutit Credit"

    def ready(self):
        from rules.profile import map_rules as profile_map_rules
        from rules.shout import map_rules as shout_map_rules

        try:
            profile_map_rules()
            shout_map_rules()
        except ProgrammingError:
            debug_logger.warning('shoutit_credit is not yet migrated, and therefore it will not function at all')
