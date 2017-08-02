from .base import CreditTransaction, CreditRule, CREDIT_RULES, CREDIT_IN, CREDIT_OUT  # NOQA
from .profile import CompleteProfile, InviteFriends, ListenToFriends  # NOQA
from .shout import ShoutPromotion, PromoteLabel, ShareShouts, PromoteShouts  # NOQA

CREDIT_RULES['complete_profile'] = CompleteProfile
CREDIT_RULES['invite_friends'] = InviteFriends
CREDIT_RULES['listen_to_friends'] = ListenToFriends
CREDIT_RULES['share_shouts'] = ShareShouts
CREDIT_RULES['promote_shouts'] = PromoteShouts
