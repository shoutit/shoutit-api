from django.conf import settings
from pusher.requests import RequestsBackend

SHOUTIT_PUSHER_SETTINGS = getattr(settings, "SHOUTIT_PUSHER_SETTINGS", {})
SHOUTIT_PUSHER_SETTINGS.setdefault("app_id", "121664")
SHOUTIT_PUSHER_SETTINGS.setdefault("key", "86d676926d4afda44089")
SHOUTIT_PUSHER_SETTINGS.setdefault("secret", "e7ef2a69a659f642fe0b")
SHOUTIT_PUSHER_SETTINGS.setdefault("ssl", True)
SHOUTIT_PUSHER_SETTINGS.setdefault("host", None)
SHOUTIT_PUSHER_SETTINGS.setdefault("port", None)
SHOUTIT_PUSHER_SETTINGS.setdefault("timeout", 5)
SHOUTIT_PUSHER_SETTINGS.setdefault("cluster", None)
SHOUTIT_PUSHER_SETTINGS.setdefault("json_encoder", None)
SHOUTIT_PUSHER_SETTINGS.setdefault("json_decoder", None)
SHOUTIT_PUSHER_SETTINGS.setdefault("backend", RequestsBackend)
