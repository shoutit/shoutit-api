from __future__ import unicode_literals

# URLS
# todo: rebase on web app
LOGIN_URL = '/signin/'
LOGOUT_URL = '/signout/'
PROFILE_URL = '/user/%s/'
SHOUT_URL = '/shout/%s/'
DEAL_URL = '/deal/%s/'
MUTE_URL = '/shout/%s/mute/'

# message headings
MESSAGE_HEAD = {
    'error': 'Oh snap!',
    'warning': 'Holy gaucamole!',
    'success': 'Well done!',
    'info': 'Heads up!'
}

DEFAULT_PAGE_SIZE = 30
DEFAULT_HOME_SHOUT_COUNT = 1000


def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type(str('Enum'), (), enums)


ENUM_XHR_RESULT = enum('SUCCESS',
                       'FAIL',
                       'BAD_REQUEST',
                       'REDIRECT',
                       'FORBIDDEN')


class Setting(object):
    def __int__(self):
        return self.value

    def __init__(self, value=0):
        self.value = value

    def __eq__(self, other):
        return self.value == int(other)

    def __hash__(self):
        return self.value


class Constant(object):
    # should be redefined inside the classes who inherited Constant
    # counter: is the number of specific type of constants
    # values: is a dict of value:text
    # texts: is a dict of text:value. if there is no text the value will be used as key
    # choices: is tuple of (value, text) used for Model choices attribute
    counter, values, texts, choices = 0, {}, {}, ()

    def __init__(self, text='', value=None):
        self.text = text
        if not value:
            self.value = self.__class__.counter
            self.__class__.counter += 1
        self.__class__.values[self.value] = text
        self.__class__.texts[text or self.value] = self.value
        self.__class__.choices += ((self.value, text),)

    def __int__(self):
        return self.value

    def __eq__(self, other):
        if other is not None:
            try:
                return self.value == int(other)
            except ValueError:
                return False
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.value

    def __str__(self):
        return self.get_text()

    def __repr__(self):
        return "<{0}: {1}>".format(self.__class__.__name__, self.get_text())

    def get_text(self):
        return self.__class__.values[self.value]


class Flag(object):
    def __int__(self):
        return self.value

    def __init__(self, text=''):
        self.value = self.__class__.counter
        self.__class__.values[self.value] = text
        self.__class__.counter *= 2

    def __hash__(self):
        return self.value

    def __str__(self):
        return self.__class__.values[self.value]

    def __and__(self, other):
        flag = self.__class__()
        flag.value = self.value & other.value
        return flag

    def __or__(self, other):
        flag = self.__class__()
        flag.value = self.value | other.value
        return flag


TOKEN_LONG = ('abcdefghkmnopqrstuvwxyzABCDEFGHKMNPQRSTUVWXYZ23456789', 24)  # for emails
TOKEN_SHORT = ('abcdefghkmnopqrstuvwxyzABCDEFGHKMNPQRSTUVWXYZ23456789', 6)  # because we can =)
TOKEN_SHORT_UPPER = ('ABCDEFGHKMNPQRSTUVWXYZ23456789', 6)  # for sms
TOKEN_SHORT_LOWER = ('abcdefghkmnopqrstuvwxyz23456789', 6)


class TokenType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


TOKEN_TYPE_EMAIL = TokenType("Email Token")
TOKEN_TYPE_NUM = TokenType("Number Token")
TOKEN_TYPE_RESET_PASSWORD = TokenType("Reset Password")
TOKEN_TYPE_EMAIL_BUSINESS_ACTIVATE = TokenType("Business Html Email Activate")
TOKEN_TYPE_EMAIL_BUSINESS_CONFIRM = TokenType("Business Html Confirm")


class FileType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


FILE_TYPE_BUSINESS_DOCUMENT = FileType("Business Document")


class BusinessConfirmationState(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


BUSINESS_CONFIRMATION_STATUS_WAITING = BusinessConfirmationState("Waiting")
BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT = BusinessConfirmationState("Waiting Payment")
BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT_CONFIRMATION = BusinessConfirmationState(
    "Waiting Payment Confirmation")
BUSINESS_CONFIRMATION_STATUS_WAITING_CONFIRMATION = BusinessConfirmationState(
    "Waiting Confirmation")
BUSINESS_CONFIRMATION_STATUS_ACCEPTED = BusinessConfirmationState("Confirmed")
BUSINESS_CONFIRMATION_STATUS_REJECTED = BusinessConfirmationState("Rejected")

business_source_types = {}


class BusinessSourceType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()

    def __init__(self, text=''):
        Constant.__init__(self, text)
        business_source_types[text] = self.value


BUSINESS_SOURCE_TYPE_NONE = BusinessSourceType('None')
BUSINESS_SOURCE_TYPE_FOURSQUARE = BusinessSourceType('Foursquare')


class UserType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


USER_TYPE_PROFILE = UserType('Profile')
USER_TYPE_PAGE = UserType('Page')


class UserState(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


# USER_STATE_INACTIVE = UserState("Inactive")
USER_STATE_ACTIVE = UserState("Active")
USER_STATE_VALID = UserState("Valid")
# USER_STATE_VERIFIED = UserState("Verified")

user_type_flags = {}


class UserTypeFlag(Flag):
    counter, values, texts, choices = 1, {}, {}, ()

    def __init__(self, text=''):
        Flag.__init__(self, text)
        user_type_flags[text] = self.value


USER_TYPE_FLAG_INDIVIDUAL = UserTypeFlag('Individual')
USER_TYPE_FLAG_BUSINESS = UserTypeFlag('Business')


class StreamType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


Stream_TYPE_PROFILE = StreamType('Profile')
Stream_TYPE_TAG = StreamType('Tag')
Stream_TYPE_BUSINESS = StreamType('Business')
Stream_TYPE_RELATED = StreamType('Related')
Stream_TYPE_RECOMMENDED = StreamType('Recommended')

rank_flags = {}


class ShoutsSortTypeFlag(Flag):
    counter = 1
    values = {}

    def __init__(self, text=''):
        Flag.__init__(self, text)
        rank_flags[text] = self.value


SORT_TYPE_TIME = ShoutsSortTypeFlag('time')
SORT_TYPE_DISTANCE = ShoutsSortTypeFlag('distance')
SORT_TYPE_PRICE_ASC = ShoutsSortTypeFlag('price_asc')
SORT_TYPE_PRICE_DESC = ShoutsSortTypeFlag('price_desc')
SORT_TYPE_RECOMMENDED = ShoutsSortTypeFlag('recommended')


class ItemState(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


ITEM_STATE_AVAILABLE = ItemState('Available')
ITEM_STATE_SOLD_OUT = ItemState('Sold Out')
ITEM_STATE_DISABLED = ItemState('Disabled')
ITEM_STATE_EXPIRED = ItemState('Expired')


class ExperienceState(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


EXPERIENCE_DOWN = ExperienceState('Thumbs down')
EXPERIENCE_UP = ExperienceState('Thumbs up')


class ConversationType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


CONVERSATION_TYPE_CHAT = ConversationType('chat')
CONVERSATION_TYPE_ABOUT_SHOUT = ConversationType('about_shout')


class MessageAttachmentType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


MESSAGE_ATTACHMENT_TYPE_SHOUT = MessageAttachmentType('shout')
MESSAGE_ATTACHMENT_TYPE_LOCATION = MessageAttachmentType('location')
MESSAGE_ATTACHMENT_TYPE_MEDIA = MessageAttachmentType('media')


class PostType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()

    def __init__(self, text=''):
        Constant.__init__(self, text)


POST_TYPE_REQUEST = PostType('request')
POST_TYPE_OFFER = PostType('offer')
POST_TYPE_EXPERIENCE = PostType('Experience')
POST_TYPE_DEAL = PostType('Deal')
POST_TYPE_EVENT = PostType('Event')

TAGS_PER_POST = 20


class NotificationType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


NOTIFICATION_TYPE_LISTEN = NotificationType('new_listen')
NOTIFICATION_TYPE_MESSAGE = NotificationType('new_message')
NOTIFICATION_TYPE_EXP_POSTED = NotificationType('Experience')
NOTIFICATION_TYPE_EXP_SHARED = NotificationType('Experience Shared')
NOTIFICATION_TYPE_COMMENT = NotificationType('Comment')


class EventType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()

    def __init__(self, text=''):
        Constant.__init__(self, text)


EVENT_TYPE_LISTEN_TO_USER = EventType('Listen to User')
EVENT_TYPE_LISTEN_TO_TAG = EventType('Listen to Tag')  # x
EVENT_TYPE_SHOUT_OFFER = EventType('Shout Offer')
EVENT_TYPE_SHOUT_REQUEST = EventType('Shout Request')
EVENT_TYPE_SHOUT_EXPERIENCE = EventType('Shout Experience')
EVENT_TYPE_SHARE_EXPERIENCE = EventType('Share Experience')
EVENT_TYPE_COMMENT = EventType('Comment')  # x
EVENT_TYPE_POST_DEAL = EventType('Post Deal')
EVENT_TYPE_BUY_DEAL = EventType('Buy Deal')
EVENT_TYPE_LISTEN_TO_PAGE = EventType('Listen to Page')

report_types = {}


class ReportType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()

    def __init__(self, text=''):
        Constant.__init__(self, text)
        report_types[text] = self.value


REPORT_TYPE_GENERAL = ReportType('general')
REPORT_TYPE_WEB_APP = ReportType('web_app')
REPORT_TYPE_IPHONE_APP = ReportType('iphone_app')
REPORT_TYPE_ANDROID_APP = ReportType('android_app')
REPORT_TYPE_USER = ReportType('user')
REPORT_TYPE_SHOUT = ReportType('shout')
REPORT_TYPE_BUSINESS = ReportType('business')
REPORT_TYPE_ITEM = ReportType('item')
REPORT_TYPE_EXPERIENCE = ReportType('experience')
REPORT_TYPE_COMMENT = ReportType('comment')

DEFAULT_LOCATIONS_LATLNG = {
    'Dubai': [25.1993957, 55.2738326],
    'Abu Dhabi': [24.4886619466, 54.3677276373],
    'Sharjah': [25.3607799496, 55.3896331787],
    'Ajman': [25.3607799496, 55.3896331787]
}

LOCATION_ATTRIBUTES = ('country', 'city', 'latitude', 'longitude')

DEFAULT_LOCATION = {
    'country': 'AE',
    'city': 'Dubai',
    'latitude': DEFAULT_LOCATIONS_LATLNG['Dubai'][0],
    'longitude': DEFAULT_LOCATIONS_LATLNG['Dubai'][1]
}

DEFAULT_CURRENCY_CODE = 'USD'


class PaymentStatus(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


PAYMENT_AUTHORIZED = PaymentStatus('Authorized')
PAYMENT_SETTLING = PaymentStatus('Settling')
PAYMENT_SETTLED = PaymentStatus('Settled')
PAYMENT_VOIDED = PaymentStatus('Voided')
PAYMENT_REFUNDED = PaymentStatus('Refunded')


class SubscriptionType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


SUBSCRIPE_BUSINESS = SubscriptionType('Business')


class SubscriptionStatus(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


SUBSCRIPTION_TRAIL = SubscriptionStatus('Trail')
SUBSCRIPTION_ACTIVE = SubscriptionStatus('Active')
SUBSCRIPTION_CANCELED = SubscriptionStatus('Canceled')
SUBSCRIPTION_EXPIRED = SubscriptionStatus('Expired')


class SMSInvitationStatus(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


SMS_INVITATION_ADDED = SMSInvitationStatus('added')
SMS_INVITATION_QUEUED = SMSInvitationStatus('queued')
SMS_INVITATION_SENT = SMSInvitationStatus('sent')
SMS_INVITATION_DELIVERED = SMSInvitationStatus('delivered')

COUNTRY_ISO = {
    "AF": "Afghanistan",
    "AX": "Aland Islands",
    "AL": "Albania",
    "DZ": "Algeria",
    "AS": "American Samoa",
    "AD": "Andorra",
    "AO": "Angola",
    "AI": "Anguilla",
    "AQ": "Antarctica",
    "AG": "Antigua and Barbuda",
    "AR": "Argentina",
    "AM": "Armenia",
    "AW": "Aruba",
    "AU": "Australia",
    "AT": "Austria",
    "AZ": "Azerbaijan",
    "BS": "Bahamas",
    "BH": "Bahrain",
    "BD": "Bangladesh",
    "BB": "Barbados",
    "BY": "Belarus",
    "BE": "Belgium",
    "BZ": "Belize",
    "BJ": "Benin",
    "BM": "Bermuda",
    "BT": "Bhutan",
    "BO": "Bolivia, Plurinational State of",
    "BQ": "Bonaire, Sint Eustatius and Saba",
    "BA": "Bosnia and Herzegovina",
    "BW": "Botswana",
    "BV": "Bouvet Island",
    "BR": "Brazil",
    "IO": "British Indian Ocean Territory",
    "BN": "Brunei Darussalam",
    "BG": "Bulgaria",
    "BF": "Burkina Faso",
    "BI": "Burundi",
    "KH": "Cambodia",
    "CM": "Cameroon",
    "CA": "Canada",
    "CV": "Cape Verde",
    "KY": "Cayman Islands",
    "CF": "Central African Republic",
    "TD": "Chad",
    "CL": "Chile",
    "CN": "China",
    "CX": "Christmas Island",
    "CC": "Cocos (Keeling) Islands",
    "CO": "Colombia",
    "KM": "Comoros",
    "CG": "Congo",
    "CD": "Congo, the Democratic Republic of the",
    "CK": "Cook Islands",
    "CR": "Costa Rica",
    "CI": "Cote d'Ivoire",
    "HR": "Croatia",
    "CU": "Cuba",
    "CW": "Curacao",
    "CY": "Cyprus",
    "CZ": "Czech Republic",
    "DK": "Denmark",
    "DJ": "Djibouti",
    "DM": "Dominica",
    "DO": "Dominican Republic",
    "EC": "Ecuador",
    "EG": "Egypt",
    "SV": "El Salvador",
    "GQ": "Equatorial Guinea",
    "ER": "Eritrea",
    "EE": "Estonia",
    "ET": "Ethiopia",
    "FK": "Falkland Islands (Malvinas)",
    "FO": "Faroe Islands",
    "FJ": "Fiji",
    "FI": "Finland",
    "FR": "France",
    "GF": "French Guiana",
    "PF": "French Polynesia",
    "TF": "French Southern Territories",
    "GA": "Gabon",
    "GM": "Gambia",
    "GE": "Georgia",
    "DE": "Germany",
    "GH": "Ghana",
    "GI": "Gibraltar",
    "GR": "Greece",
    "GL": "Greenland",
    "GD": "Grenada",
    "GP": "Guadeloupe",
    "GU": "Guam",
    "GT": "Guatemala",
    "GG": "Guernsey",
    "GN": "Guinea",
    "GW": "Guinea-Bissau",
    "GY": "Guyana",
    "HT": "Haiti",
    "HM": "Heard Island and McDonald Islands",
    "VA": "Holy See (Vatican City State)",
    "HN": "Honduras",
    "HK": "Hong Kong",
    "HU": "Hungary",
    "IS": "Iceland",
    "IN": "India",
    "ID": "Indonesia",
    "IR": "Iran, Islamic Republic of",
    "IQ": "Iraq",
    "IE": "Ireland",
    "IM": "Isle of Man",
    "IL": "Israel",
    "IT": "Italy",
    "JM": "Jamaica",
    "JP": "Japan",
    "JE": "Jersey",
    "JO": "Jordan",
    "KZ": "Kazakhstan",
    "KE": "Kenya",
    "KI": "Kiribati",
    "KP": "Korea, Democratic People's Republic of",
    "KR": "Korea, Republic of",
    "KW": "Kuwait",
    "KG": "Kyrgyzstan",
    "LA": "Lao People's Democratic Republic",
    "LV": "Latvia",
    "LB": "Lebanon",
    "LS": "Lesotho",
    "LR": "Liberia",
    "LY": "Libya",
    "LI": "Liechtenstein",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MO": "Macao",
    "MK": "Macedonia, the former Yugoslav Republic of",
    "MG": "Madagascar",
    "MW": "Malawi",
    "MY": "Malaysia",
    "MV": "Maldives",
    "ML": "Mali",
    "MT": "Malta",
    "MH": "Marshall Islands",
    "MQ": "Martinique",
    "MR": "Mauritania",
    "MU": "Mauritius",
    "YT": "Mayotte",
    "MX": "Mexico",
    "FM": "Micronesia, Federated States of",
    "MD": "Moldova, Republic of",
    "MC": "Monaco",
    "MN": "Mongolia",
    "ME": "Montenegro",
    "MS": "Montserrat",
    "MA": "Morocco",
    "MZ": "Mozambique",
    "MM": "Myanmar",
    "NA": "Namibia",
    "NR": "Nauru",
    "NP": "Nepal",
    "NL": "Netherlands",
    "NC": "New Caledonia",
    "NZ": "New Zealand",
    "NI": "Nicaragua",
    "NE": "Niger",
    "NG": "Nigeria",
    "NU": "Niue",
    "NF": "Norfolk Island",
    "MP": "Northern Mariana Islands",
    "NO": "Norway",
    "OM": "Oman",
    "PK": "Pakistan",
    "PW": "Palau",
    "PS": "Palestinian Territory, Occupied",
    "PA": "Panama",
    "PG": "Papua New Guinea",
    "PY": "Paraguay",
    "PE": "Peru",
    "PH": "Philippines",
    "PN": "Pitcairn",
    "PL": "Poland",
    "PT": "Portugal",
    "PR": "Puerto Rico",
    "QA": "Qatar",
    "RE": "Reunion",
    "RO": "Romania",
    "RU": "Russian Federation",
    "RW": "Rwanda",
    "BL": "Saint Barthelemy",
    "SH": "Saint Helena, Ascension and Tristan da Cunha",
    "KN": "Saint Kitts and Nevis",
    "LC": "Saint Lucia",
    "MF": "Saint Martin (French part)",
    "PM": "Saint Pierre and Miquelon",
    "VC": "Saint Vincent and the Grenadines",
    "WS": "Samoa",
    "SM": "San Marino",
    "ST": "Sao Tome and Principe",
    "SA": "Saudi Arabia",
    "SN": "Senegal",
    "RS": "Serbia",
    "SC": "Seychelles",
    "SL": "Sierra Leone",
    "SG": "Singapore",
    "SX": "Sint Maarten (Dutch part)",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "SB": "Solomon Islands",
    "SO": "Somalia",
    "ZA": "South Africa",
    "GS": "South Georgia and the South Sandwich Islands",
    "SS": "South Sudan",
    "ES": "Spain",
    "LK": "Sri Lanka",
    "SD": "Sudan",
    "SR": "Suriname",
    "SJ": "Svalbard and Jan Mayen",
    "SZ": "Swaziland",
    "SE": "Sweden",
    "CH": "Switzerland",
    "SY": "Syrian Arab Republic",
    "TW": "Taiwan, Province of China",
    "TJ": "Tajikistan",
    "TZ": "Tanzania, United Republic of",
    "TH": "Thailand",
    "TL": "Timor-Leste",
    "TG": "Togo",
    "TK": "Tokelau",
    "TO": "Tonga",
    "TT": "Trinidad and Tobago",
    "TN": "Tunisia",
    "TR": "Turkey",
    "TM": "Turkmenistan",
    "TC": "Turks and Caicos Islands",
    "TV": "Tuvalu",
    "UG": "Uganda",
    "UA": "Ukraine",
    "AE": "United Arab Emirates",
    "GB": "United Kingdom",
    "US": "United States",
    "UM": "United States Minor Outlying Islands",
    "UY": "Uruguay",
    "UZ": "Uzbekistan",
    "VU": "Vanuatu",
    "VE": "Venezuela, Bolivarian Republic of",
    "VN": "Viet Nam",
    "VG": "Virgin Islands, British",
    "VI": "Virgin Islands, U.S.",
    "WF": "Wallis and Futuna",
    "EH": "Western Sahara",
    "YE": "Yemen",
    "ZM": "Zambia",
    "ZW": "Zimbabwe",
    "": "None"
}

NOT_ALLOWED_USERNAMES = [
    'activate',
    'admin',
    'admins',
    'api',
    'bad-experience',
    'bad-experiences',
    'bsignup',
    'btempsignup',
    'buy',
    'buys',
    'close_deal',
    'comment',
    'comments',
    'confirm_business',
    'contact-import',
    'cpsp_',
    'create_tiny_business',
    'deal',
    'deals',
    'deleteConversation',
    'deleteMessage',
    'experience',
    'experiences',
    'fb_auth',
    'fb',
    'gallery',
    'galleries',
    'good-experience',
    'good-experiences',
    'googlebc700f17ba42dd9f.html',
    'gplus_auth',
    'grappelli',
    'image',
    'images',
    'invalidate_voucher',
    'item',
    'items',
    'jsi18n',
    'learnmore',
    'link',
    'links',
    'me',
    'messages',
    'message',
    'modal',
    'notifications',
    'notification',
    'oauth',
    'offer',
    'offers',
    'paypal_return',
    'paypal',
    'privacy',
    'reactivate',
    'recover_business_activation',
    'recover',
    'reply',
    'replies',
    'report',
    'reports',
    'request',
    'requests',
    'robots.txt',
    'rule',
    'rules',
    'sell',
    'sells',
    'send_invitations',
    'shout_deal',
    'shout',
    'shouts',
    'signin',
    'signout',
    'signup',
    'sts',
    'subscribe',
    'tag',
    'tags',
    'tos',
    'top_tags',
    'upload',
    'user',
    'users',
    'valid_voucher',
    'xhr',
]
