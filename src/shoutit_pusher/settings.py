import os

from django.conf import settings
from pusher.requests import RequestsBackend

SHOUTIT_PUSHER_SETTINGS = {}
PUSHER_ENV = settings.PUSHER_ENV
if PUSHER_ENV == 'prod':
    # shoutit-api-prod
    SHOUTIT_PUSHER_SETTINGS["app_id"] = "121664"
    SHOUTIT_PUSHER_SETTINGS["key"] = "86d676926d4afda44089"
    SHOUTIT_PUSHER_SETTINGS["secret"] = "e7ef2a69a659f642fe0b"
elif PUSHER_ENV == 'dev':
    # shoutit-api-dev
    SHOUTIT_PUSHER_SETTINGS["app_id"] = "193632"
    SHOUTIT_PUSHER_SETTINGS["key"] = "7bee1e468fabb6287fc5"
    SHOUTIT_PUSHER_SETTINGS["secret"] = "727dcefd63d526113aa5"
else:
    # shoutit-api-local
    SHOUTIT_PUSHER_SETTINGS["app_id"] = "193590"
    SHOUTIT_PUSHER_SETTINGS["key"] = "d6a98f27e49289344791"
    SHOUTIT_PUSHER_SETTINGS["secret"] = "5ac1c01bc04e90c13339"
SHOUTIT_PUSHER_SETTINGS["ssl"] = True
SHOUTIT_PUSHER_SETTINGS["host"] = None
SHOUTIT_PUSHER_SETTINGS["port"] = None
SHOUTIT_PUSHER_SETTINGS["timeout"] = 5
SHOUTIT_PUSHER_SETTINGS["cluster"] = None
SHOUTIT_PUSHER_SETTINGS["json_encoder"] = None
SHOUTIT_PUSHER_SETTINGS["json_decoder"] = None
SHOUTIT_PUSHER_SETTINGS["backend"] = RequestsBackend
