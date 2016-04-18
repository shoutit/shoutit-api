from django.conf import settings
from pusher.requests import RequestsBackend

SHOUTIT_PUSHER_SETTINGS = getattr(settings, "SHOUTIT_PUSHER_SETTINGS", {})
if settings.PROD:
    # shoutit-api-prod
    SHOUTIT_PUSHER_SETTINGS.setdefault("app_id", "121664")
    SHOUTIT_PUSHER_SETTINGS.setdefault("key", "86d676926d4afda44089")
    SHOUTIT_PUSHER_SETTINGS.setdefault("secret", "e7ef2a69a659f642fe0b")
elif settings.DEV:
    # shoutit-api-dev
    SHOUTIT_PUSHER_SETTINGS.setdefault("app_id", "193632")
    SHOUTIT_PUSHER_SETTINGS.setdefault("key", "7bee1e468fabb6287fc5")
    SHOUTIT_PUSHER_SETTINGS.setdefault("secret", "727dcefd63d526113aa5")
else:
    # shoutit-api-local
    SHOUTIT_PUSHER_SETTINGS.setdefault("app_id", "193590")
    SHOUTIT_PUSHER_SETTINGS.setdefault("key", "d6a98f27e49289344791")
    SHOUTIT_PUSHER_SETTINGS.setdefault("secret", "5ac1c01bc04e90c13339")
SHOUTIT_PUSHER_SETTINGS.setdefault("ssl", True)
SHOUTIT_PUSHER_SETTINGS.setdefault("host", None)
SHOUTIT_PUSHER_SETTINGS.setdefault("port", None)
SHOUTIT_PUSHER_SETTINGS.setdefault("timeout", 5)
SHOUTIT_PUSHER_SETTINGS.setdefault("cluster", None)
SHOUTIT_PUSHER_SETTINGS.setdefault("json_encoder", None)
SHOUTIT_PUSHER_SETTINGS.setdefault("json_decoder", None)
SHOUTIT_PUSHER_SETTINGS.setdefault("backend", RequestsBackend)
