from django.conf import settings
from pusher.requests import RequestsBackend

SHOUTIT_PUSHER_SETTINGS = {
    "ssl": True,
    "host": None,
    "port": None,
    "timeout": 5,
    "cluster": None,
    "json_encoder": None,
    "json_decoder": None,
    "backend": RequestsBackend
}
PUSHER_ENV = settings.PUSHER_ENV

if PUSHER_ENV == 'live':
    SHOUTIT_PUSHER_SETTINGS["app_id"] = "121664"
    SHOUTIT_PUSHER_SETTINGS["key"] = "86d676926d4afda44089"
    SHOUTIT_PUSHER_SETTINGS["secret"] = "e7ef2a69a659f642fe0b"
elif PUSHER_ENV == 'stage':
    SHOUTIT_PUSHER_SETTINGS["app_id"] = "193632"
    SHOUTIT_PUSHER_SETTINGS["key"] = "7bee1e468fabb6287fc5"
    SHOUTIT_PUSHER_SETTINGS["secret"] = "727dcefd63d526113aa5"
else:
    SHOUTIT_PUSHER_SETTINGS["app_id"] = "193590"
    SHOUTIT_PUSHER_SETTINGS["key"] = "d6a98f27e49289344791"
    SHOUTIT_PUSHER_SETTINGS["secret"] = "5ac1c01bc04e90c13339"
