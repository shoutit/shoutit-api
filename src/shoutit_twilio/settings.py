from django.conf import settings

SHOUTIT_TWILIO_SETTINGS = getattr(settings, "SHOUTIT_PUSHER_SETTINGS", {})
SHOUTIT_TWILIO_SETTINGS.setdefault("TWILIO_ACCOUNT_SID", "AC72062980c854618cfa7765121af3085d")
if getattr(settings, 'PROD', False):
    SHOUTIT_TWILIO_SETTINGS.setdefault("TWILIO_API_KEY", "SK4717f4a7929e0a0224f120acc6a26f5c")
    SHOUTIT_TWILIO_SETTINGS.setdefault("TWILIO_API_SECRET", "y5WHQH2qd9crtNLuOMx3uoxQ5FJUXZsQ")
else:
    SHOUTIT_TWILIO_SETTINGS.setdefault("TWILIO_API_KEY", "SK701ec111c6e494e9e0fa964c2999507d")
    SHOUTIT_TWILIO_SETTINGS.setdefault("TWILIO_API_SECRET", "AVEqTWt74kA0aFi9NB8TDTShPHb5LaFO")
if getattr(settings, 'PROD', False):
    SHOUTIT_TWILIO_SETTINGS.setdefault("TWILIO_CONFIGURATION_SID", "VS32da2a0f9dbfe4196f4301331e28bfe7")
else:
    SHOUTIT_TWILIO_SETTINGS.setdefault("TWILIO_CONFIGURATION_SID", "VS62cb86639806a479f8637eeb98eb80ff")
