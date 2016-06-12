from __future__ import unicode_literals
from django.apps import AppConfig


class ShoutitCreditConfig(AppConfig):
    name = 'shoutit_credit'
    label = 'shoutit_credit'
    verbose_name = "Shoutit Credit"

    def ready(self):
        from rules.profile import map_rules as profile_map_rules
        from rules.shout import map_rules as shout_map_rules

        profile_map_rules()
        shout_map_rules()
