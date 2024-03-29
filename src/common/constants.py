class Constant(object):
    """
    should be redefined inside the classes who inherited Constant
    counter: is the number of specific type of constants
    values: is a dict of value:text
    texts: is a dict of text:value. if there is no text the value will be used as key
    choices: is tuple of (value, text) used for Model choices attribute
    """
    counter, values, texts, choices = 0, {}, {}, ()

    def __init__(self, text='', value=None):
        self.text = text
        if value is not None:
            self.value = value
        else:
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

    @classmethod
    def instance(cls, value):
        return cls(cls.values[value], value)


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


class DeviceOS(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


DEVICE_ANDROID = DeviceOS("android")
DEVICE_IOS = DeviceOS("ios")


class BusinessConfirmationState(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


BUSINESS_CONFIRMATION_STATUS_WAITING = BusinessConfirmationState("Waiting")
BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT = BusinessConfirmationState("Waiting Payment")
BUSINESS_CONFIRMATION_STATUS_WAITING_PAYMENT_CONFIRMATION = BusinessConfirmationState("Waiting Payment Confirmation")
BUSINESS_CONFIRMATION_STATUS_WAITING_CONFIRMATION = BusinessConfirmationState("Waiting Confirmation")
BUSINESS_CONFIRMATION_STATUS_ACCEPTED = BusinessConfirmationState("Confirmed")
BUSINESS_CONFIRMATION_STATUS_REJECTED = BusinessConfirmationState("Rejected")


class BusinessSourceType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


BUSINESS_SOURCE_TYPE_NONE = BusinessSourceType('None')
BUSINESS_SOURCE_TYPE_FOURSQUARE = BusinessSourceType('Foursquare')


class UserType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


USER_TYPE_PROFILE = UserType('Profile')
USER_TYPE_PAGE = UserType('Page')


class PageAdminType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


PAGE_ADMIN_TYPE_OWNER = PageAdminType('owner')
PAGE_ADMIN_TYPE_ADMIN = PageAdminType('admin')
PAGE_ADMIN_TYPE_EDITOR = PageAdminType('editor')


class ItemState(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


ITEM_STATE_AVAILABLE = ItemState('Available')
ITEM_STATE_SOLD_OUT = ItemState('Sold Out')
ITEM_STATE_DISABLED = ItemState('Disabled')
ITEM_STATE_EXPIRED = ItemState('Expired')


class ConversationType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


CONVERSATION_TYPE_CHAT = ConversationType('chat')
CONVERSATION_TYPE_ABOUT_SHOUT = ConversationType('about_shout')
CONVERSATION_TYPE_PUBLIC_CHAT = ConversationType('public_chat')


class MessageAttachmentType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


MESSAGE_ATTACHMENT_TYPE_SHOUT = MessageAttachmentType('shout')
MESSAGE_ATTACHMENT_TYPE_LOCATION = MessageAttachmentType('location')
MESSAGE_ATTACHMENT_TYPE_MEDIA = MessageAttachmentType('media')
MESSAGE_ATTACHMENT_TYPE_PROFILE = MessageAttachmentType('profile')


class PostType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


POST_TYPE_REQUEST = PostType('request')
POST_TYPE_OFFER = PostType('offer')

MAX_TAGS_PER_SHOUT = 5


class TagValueType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


TAG_TYPE_INT = TagValueType('int')
TAG_TYPE_STR = TagValueType('str')


class NotificationType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()

    @classmethod
    def new_notification(cls):
        return cls('new_notification', 1000)

    def requires_notification_object(self):
        types = [
            NOTIFICATION_TYPE_MESSAGE,
            NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_BROADCAST, NOTIFICATION_TYPE_MISSED_VIDEO_CALL,
            NOTIFICATION_TYPE_CREDIT_TRANSACTION
        ]
        return self in types

    def is_new_notification_type(self):
        types = [
            NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_BROADCAST, NOTIFICATION_TYPE_MISSED_VIDEO_CALL
        ]
        return self in types

    def is_new_notification_push_type(self):
        types = [
            NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_BROADCAST, NOTIFICATION_TYPE_MISSED_VIDEO_CALL,
            NOTIFICATION_TYPE_CREDIT_TRANSACTION
        ]
        return self in types

    def include_in_push(self):
        types = [NOTIFICATION_TYPE_INCOMING_VIDEO_CALL]
        return self in types or self.requires_notification_object()

    def include_in_email(self):
        types = [NOTIFICATION_TYPE_MESSAGE, NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_CREDIT_TRANSACTION]
        return self in types


NOTIFICATION_TYPE_LISTEN = NotificationType('new_listen')
NOTIFICATION_TYPE_MESSAGE = NotificationType('new_message')
NOTIFICATION_TYPE_BROADCAST = NotificationType('broadcast')
NOTIFICATION_TYPE_PROFILE_UPDATE = NotificationType('profile_update')
NOTIFICATION_TYPE_CONVERSATION_UPDATE = NotificationType('conversation_update')
NOTIFICATION_TYPE_READ_BY = NotificationType('new_read_by')
NOTIFICATION_TYPE_STATS_UPDATE = NotificationType('stats_update')
NOTIFICATION_TYPE_INCOMING_VIDEO_CALL = NotificationType('incoming_video_call')
NOTIFICATION_TYPE_MISSED_VIDEO_CALL = NotificationType('missed_video_call')
NOTIFICATION_TYPE_CREDIT_TRANSACTION = NotificationType('new_credit_transaction')
NOTIFICATION_TYPE_SHOUT_LIKE = NotificationType('new_shout_like')


class ListenType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


LISTEN_TYPE_PROFILE = ListenType('Profile')
LISTEN_TYPE_PAGE = ListenType('Page')
LISTEN_TYPE_TAG = ListenType('Tag')


class ReportType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


REPORT_TYPE_GENERAL = ReportType('general')
REPORT_TYPE_WEB_APP = ReportType('web_app')
REPORT_TYPE_IPHONE_APP = ReportType('iphone_app')
REPORT_TYPE_ANDROID_APP = ReportType('android_app')
REPORT_TYPE_PROFILE = ReportType('profile')
REPORT_TYPE_SHOUT = ReportType('shout')
REPORT_TYPE_CONVERSATION = ReportType('conversation')

DEFAULT_LOCATIONS_LATLNG = {
    'Dubai': [25.1993957, 55.2738326],
    'Abu Dhabi': [24.4886619466, 54.3677276373],
    'Sharjah': [25.3607799496, 55.3896331787],
    'Ajman': [25.3607799496, 55.3896331787]
}

LOCATION_ATTRIBUTES = ('country', 'city', 'latitude', 'longitude')

DEFAULT_LOCATION = {
    'country': 'AE',
    'postal_code': 'Dubai',
    'state': 'Dubai',
    'city': 'Dubai',
    'address': '',
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
SMS_INVITATION_PARKED = SMSInvitationStatus('parked')
SMS_INVITATION_ERROR = SMSInvitationStatus('error')

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

COUNTRIES = COUNTRY_ISO.keys()

COUNTRY_CHOICES = sorted(COUNTRY_ISO.items(), key=lambda tup: tup[1])

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
    # Todo (mo): Add more
]

PROFANITIES_LIST = (
    'ass', 'ass lick', 'asses', 'asshole', 'assholes', 'asskisser', 'asswipe',
    'balls', 'bastard', 'beastial', 'beastiality', 'beastility', 'beaver',
    'belly whacker', 'bestial', 'bestiality', 'bitch', 'bitcher', 'bitchers',
    'bitches', 'bitchin', 'bitching', 'blow job', 'blowjob', 'blowjobs', 'bonehead',
    'boner', 'brown eye', 'browneye', 'browntown', 'bucket cunt', 'bull shit',
    'bullshit', 'bum', 'bung hole', 'butch', 'butt', 'butt breath', 'butt fucker',
    'butt hair', 'buttface', 'buttfuck', 'buttfucker', 'butthead', 'butthole',
    'buttpicker', 'chink', 'circle jerk', 'clam', 'clit', 'cobia', 'cock', 'cocks',
    'cocksuck', 'cocksucked', 'cocksucker', 'cocksucking', 'cocksucks', 'cooter',
    'crap', 'cum', 'cummer', 'cumming', 'cums', 'cumshot', 'cunilingus',
    'cunillingus', 'cunnilingus', 'cunt', 'cuntlick', 'cuntlicker', 'cuntlicking',
    'cunts', 'cyberfuc', 'cyberfuck', 'cyberfucked', 'cyberfucker', 'cyberfuckers',
    'cyberfucking', 'damn', 'dick', 'dike', 'dildo', 'dildos', 'dink', 'dinks',
    'dipshit', 'dong', 'douche bag', 'dumbass', 'dyke', 'ejaculate', 'ejaculated',
    'ejaculates', 'ejaculating', 'ejaculatings', 'ejaculation', 'fag', 'fagget',
    'fagging', 'faggit', 'faggot', 'faggs', 'fagot', 'fagots', 'fags', 'fart',
    'farted', 'farting', 'fartings', 'farts', 'farty', 'fatass', 'fatso',
    'felatio', 'fellatio', 'fingerfuck', 'fingerfucked', 'fingerfucker',
    'fingerfuckers', 'fingerfucking', 'fingerfucks', 'fistfuck', 'fistfucked',
    'fistfucker', 'fistfuckers', 'fistfucking', 'fistfuckings', 'fistfucks',
    'fuck', 'fucked', 'fucker', 'fuckers', 'fuckin', 'fucking', 'fuckings',
    'fuckme', 'fucks', 'fuk', 'fuks', 'furburger', 'gangbang', 'gangbanged',
    'gangbangs', 'gaysex', 'gazongers', 'goddamn', 'gonads', 'gook', 'guinne',
    'hard on', 'hardcoresex', 'homo', 'hooker', 'horniest', 'horny', 'hotsex',
    'hussy', 'jack off', 'jackass', 'jacking off', 'jackoff', 'jack-off', 'jap',
    'jerk', 'jerk-off', 'jism', 'jiz', 'jizm', 'jizz', 'kike', 'kock', 'kondum',
    'kondums', 'kraut', 'kum', 'kummer', 'kumming', 'kums', 'kunilingus', 'lesbian',
    'lesbo', 'merde', 'mick', 'mothafuck', 'mothafucka', 'mothafuckas',
    'mothafuckaz', 'mothafucked', 'mothafucker', 'mothafuckers', 'mothafuckin',
    'mothafucking', 'mothafuckings', 'mothafucks', 'motherfuck', 'motherfucked',
    'motherfucker', 'motherfuckers', 'motherfuckin', 'motherfucking',
    'motherfuckings', 'motherfucks', 'muff', 'nigger', 'niggers', 'orgasim',
    'orgasims', 'orgasm', 'orgasms', 'pecker', 'penis', 'phonesex', 'phuk',
    'phuked', 'phuking', 'phukked', 'phukking', 'phuks', 'phuq', 'pimp', 'piss',
    'pissed', 'pissrr', 'pissers', 'pisses', 'pissin', 'pissing', 'pissoff',
    'prick', 'pricks', 'pussies', 'pussy', 'pussys', 'queer', 'retard', 'schlong',
    'screw', 'sheister', 'shit', 'shited', 'shitfull', 'shiting', 'shitings',
    'shits', 'shitted', 'shitter', 'shitters', 'shitting', 'shittings', 'shitty',
    'slag', 'sleaze', 'slut', 'sluts', 'smut', 'snatch', 'spunk', 'twat', 'wetback',
    'whore', 'wop',
)
