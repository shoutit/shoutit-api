# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, print_function
from .settings_env import *
from common.utils import get_address_port, check_offline_mood

OFFLINE_MODE = check_offline_mood()
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/
SECRET_KEY = '0af3^t(o@8cl(8z_gli1@)j*)&(&qzlvu7gox@koj-e#u8z*$q'

# using gunicorn or not
GUNICORN = 'gunicorn' in os.environ.get('SERVER_SOFTWARE', '')
ADDRESS, PORT = get_address_port(GUNICORN)

info("==================================================")
info("================= Shoutit Server =================")
info("==================================================")
info("ENV:", ENV)
if OFFLINE_MODE:
    info("OFFLINE MODE: ON")
info("GUNICORN:", GUNICORN)
info("BIND: {}:{}".format(ADDRESS, PORT))

if PROD:
    DEBUG = False
    SHOUT_IT_DOMAIN = 'www.shoutit.com'
    SHOUT_IT_HOST = 'shoutit.com'
    SITE_LINK = 'https://www.shoutit.com/'
    API_LINK = 'https://api.shoutit.com/v2/'

elif DEV:
    DEBUG = True
    SHOUT_IT_DOMAIN = 'dev.shoutit.com'
    SHOUT_IT_HOST = 'dev.shoutit.com'
    SITE_LINK = 'http://dev.www.shoutit.com/'
    API_LINK = 'http://dev.api.shoutit.com/v2/'

else:  # LOCAL
    DEBUG = True
    SHOUT_IT_DOMAIN = 'shoutit.dev:8000'
    SHOUT_IT_HOST = 'shoutit.dev'
    SITE_LINK = 'http://shoutit.dev:3000/'
    API_LINK = 'http://shoutit.dev:8000/v2/'

info("DEBUG:", DEBUG)
info("SITE_LINK:", SITE_LINK)
info("API_LINK:", API_LINK)

# URLs
ROOT_URLCONF = 'shoutit.urls'
APPEND_SLASH = False
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
WSGI_APPLICATION = 'shoutit.wsgi.application'

TEMPLATE_DEBUG = DEBUG
ALLOWED_HOSTS = ['127.0.0.1', 'shoutit.dev', '.shoutit.com.', '.shoutit.com']
INTERNAL_IPS = ('127.0.0.1', 'shoutit.dev')
ADMINS = (
    ('Mo Chawich', 'mo.chawich@gmail.com'),
)
MANAGERS = ADMINS

# Shoutit defaults
MAX_REG_DAYS = 14
MAX_SHOUTS_INACTIVE_USER = 5
MAX_EXPIRY_DAYS_SSS = 7
FORCE_SSS_NOTIFY = True
SHOUT_EXPIRY_NOTIFY = 2
MAX_EXPIRY_DAYS = 60
ACCOUNT_ACTIVATION_DAYS = 7
NEARBY_CITIES_RADIUS_KM = 65

"""
=================================
            Caching
=================================
"""
# Redis
SESSION_REDIS_HOST = 'redis.shoutit.com'
SESSION_REDIS_PORT = 6379
SESSION_REDIS_DB = 1  # redis_db
SESSION_REDIS_PREFIX = ENV + '_session'
REDIS_SESSION_ENGINE = 'redis_sessions.session'
REDIS_CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': 'redis.shoutit.com:6379',
        'TIMEOUT': 12 * 60 * 60,
        'OPTIONS': {
            'DB': 2,  # redis_db
        },
        'KEY_PREFIX': ENV + '_cache'
    }
}
# todo: set passwords for redis

SESSION_ENGINE = REDIS_SESSION_ENGINE
CACHES = REDIS_CACHES

"""
=================================
           Queuing
=================================
"""
FORCE_SYNC_RQ = False
RQ_QUEUE = ENV
RQ_QUEUES = {
    RQ_QUEUE: {
        'USE_REDIS_CACHE': 'default',
        'DEFAULT_TIMEOUT': 30,
    },
}
if DEBUG or FORCE_SYNC_RQ:
    for queue_config in RQ_QUEUES.itervalues():
        queue_config['ASYNC'] = False

"""
=================================
           AntiCaptcha
=================================
"""
ANTI_KEY = 'eb8e82bf16467103e8e0f49f6ea2924a'

"""
=================================
          Elasticsearch
=================================
"""
from elasticsearch_dsl.connections import connections
# Define a default global Elasticsearch client
ES = connections.create_connection(hosts=['es.shoutit.com'])

AUTH_USER_MODEL = 'shoutit.User'

# Application definition
INSTALLED_APPS = (
    'grappelli',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    # 'paypal.standard.ipn',
    # 'paypal.standard.pdt',
    # 'keyedcache',
    # 'livesettings',
    # 'l10n',
    # 'payment',
    # 'subscription',

    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_swagger',
    'provider',
    'provider.oauth2',

    'push_notifications',

    'django_rq',
    'widget_tweaks',
    'corsheaders',

    'shoutit_pusher',
    'shoutit',
)
# apps only on local development
if LOCAL:
    INSTALLED_APPS += (
    )
# apps on on server [dev, prod]
if ON_SERVER:
    INSTALLED_APPS += (
    )
# apps only on server development
if DEV:
    INSTALLED_APPS += (
    )
# apps only on server production
if PROD:
    INSTALLED_APPS += (
    )

RAVEN_CONFIG = {
    'dsn': 'requests+https://b26adb7e1a3b46dabc1b05bc8355008d:b820883c74724dcb93753af31cb21ee4@app.getsentry.com/36984',
    'string_max_length': 1000
}

APNS_SANDBOX = False
FORCE_PUSH = False
PUSH_NOTIFICATIONS_SETTINGS = {
    'GCM_API_KEY': "AIzaSyBld5731YUMSNuLBO5Gu2L4Tsj-CrQZGIg",
    'APNS_CERTIFICATE': os.path.join(API_DIR, 'assets', 'certificates', 'ios', 'push-%s.pem'
                                     % ('dev' if APNS_SANDBOX else 'prod')),
    'APNS_HOST': "gateway.%spush.apple.com" % ('sandbox.' if APNS_SANDBOX else ''),
    'APNS_FEEDBACK_HOST': "feedback.%spush.apple.com" % ('sandbox.' if APNS_SANDBOX else '')
}
info('FORCE_PUSH:', FORCE_PUSH)
info('APNS_SANDBOX:', APNS_SANDBOX)

CORS_ORIGIN_ALLOW_ALL = True

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    # Shoutit Custom Middleware
    'shoutit.middleware.APIDetectionMiddleware',
    'shoutit.middleware.JsonPostMiddleware',
    'shoutit.middleware.UserPermissionsMiddleware',
    'shoutit.middleware.FBMiddleware',
    # 'common.middleware.ProfilerMiddleware.ProfileMiddleware',
    # 'common.middleware.SqlLogMiddleware.SQLLogToConsoleMiddleware',
)

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': ENV.replace('_api', ''),  # eg. ENV is shoutit_api_pro, db should be shoutit_prod
        'USER': 'shoutit',
        'PASSWORD': '#a\_Y9>uw<.5;_=/kUwK',
        'HOST': 'db.shoutit.com',
        'PORT': '5432',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = False

ugettext = lambda s: s
LANGUAGES = (
    ('en', ugettext('English')),
)
DEFAULT_LANGUAGE_CODE = 'en'


# Static files (CSS, JavaScript, Images)
FORCE_S3 = True
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

AWS_ACCESS_KEY_ID = 'AKIAIWBSACXFWBQ3MGWA'
AWS_SECRET_ACCESS_KEY = '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'
if ON_SERVER or FORCE_S3:
    INSTALLED_APPS += (
        'storages',
    )
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    AWS_STORAGE_BUCKET_NAME = 'shoutit-api-static'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    STATIC_URL = "https://%s/" % AWS_S3_CUSTOM_DOMAIN
else:
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(ENV_DIR, 'static')

STATICFILES_DIRS = (
    os.path.join(DJANGO_DIR, 'static'),
)

info('FORCE_S3:', FORCE_S3)
info('STATIC_URL:', STATIC_URL)

# Templates
TEMPLATE_DIRS = (
    os.path.join(DJANGO_DIR, 'templates', 'api_site'),
    os.path.join(DJANGO_DIR, 'templates', 'text_messages'),
    os.path.join(DJANGO_DIR, 'templates', 'html_messages'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    "shoutit.middleware.default_location",
    "shoutit.middleware.include_settings",
)

GRAPPELLI_ADMIN_TITLE = 'Shoutit'

LOG_SQL = False

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s] [%(levelname)s]: %(message)s'
        },
        'simple_dashed': {
            'format': '-------------------------------------------\n'
                      '[%(asctime)s] [%(levelname)s]: %(message)s\n'
                      '-------------------------------------------'
        },
        'detailed': {
            'format': '[%(asctime)s] [%(levelname)s] in %(pathname)s:%(lineno)s:%(funcName)s: %(message)s'
        },
        'message_only': {
            'format': '%(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'level_below_warning': {
            '()': 'common.log.LevelBelowWarning',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
            'formatter': 'detailed'
        },
        'console_err': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
            'formatter': 'detailed'
        },
        'console_out': {
            'level': 'DEBUG' if LOCAL and LOG_SQL else 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'filters': ['level_below_warning'],
            'formatter': 'simple'
        },
        'console_out_all': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'simple',
        },
        'console_err_all': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
            'formatter': 'detailed',
            'filters': ['require_debug_true'],
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler',
            'filters': ['require_debug_false'],
        },
        'sentry_all': {
            'level': 'DEBUG',
            'class': 'raven.contrib.django.handlers.SentryHandler',
            'filters': ['require_debug_false'],
        },
        'sentry_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'sentry.err.log'),
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
            'include_html': False,
        },
        'sql_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'filename': os.path.join(LOG_DIR, 'sql.log')
        },
        'sss_file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'filename': os.path.join(LOG_DIR, 'sss.log'),
            'formatter': 'simple_dashed'
        },
        'sql_console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'message_only'
        },
        'null': {
            "class": 'django.utils.log.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console_out', 'console_err', 'sentry'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ['console_err', 'sentry'],
            'propagate': False,
        },
        'raven': {
            'level': 'WARNING',
            'handlers': ['sentry_file'],
            'propagate': False,
        },
        'sentry': {
            'level': 'WARNING',
            'handlers': ['sentry_file'],
            'propagate': False,
        },
        'gunicorn': {
            'level': 'DEBUG',
            'handlers': ['console_out', 'console_err', 'sentry'],
            'propagate': False,
        },
        'rq.worker': {
            'handlers': ['console_out', 'console_err', 'sentry'],
            "level": "DEBUG",
            'propagate': False,
        },
        # 'requests': {
        # 'level': 'DEBUG',
        # 'handlers': ['console_out', 'console_err', 'sentry'],
        # },

        'SqlLogMiddleware': {
            'handlers': ['sql_file'],
            'level': 'INFO',
            'propagate': False
        },
        'SqlLogMiddleware_console': {
            'handlers': ['sql_console'],
            'level': 'INFO',
            'propagate': False
        },
        'shoutit': {
            'handlers': ['console_out_all'],
            'level': 'DEBUG',
            'propagate': False
        },
        'shoutit.error': {
            'handlers': ['console_err_all', 'sentry_all'],
            'level': 'DEBUG',
            'propagate': False
        },
        'shoutit.sss': {
            'handlers': ['sss_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        '': {
            'handlers': ['console_out', 'console_err', 'sentry'],
        },
    }
}

# Mixpanel
MIXPANEL_TOKEN = 'c9d0a1dc521ac1962840e565fa971574'
FORCE_MP_TRACKING = False

# IP2Location
IP2LOCATION_DB_BIN = os.path.join(API_DIR, 'assets', 'ip2location', 'IP2LOCATION-LITE-DB9.BIN')

# Twilio
TWILIO_ACCOUNT_SID = "AC72062980c854618cfa7765121af3085d"
TWILIO_AUTH_TOKEN = "ed5a3b1dc6debc010e10047ebaa066ce"
TWILIO_FROM = '+14807255600'

# Mail Settings
MAILCHIMP_API_KEY = 'd87a573a48bc62ff3326d55f6a92b2cc-us5'
MAILCHIMP_MASTER_LIST_ID = 'f339e70dd9'

FORCE_SMTP = False

GOOGLE_SMTP = {
    'default_from_email': 'Jack <reply@shoutit.com>',
    'host': 'smtp.gmail.com',
    'port': 587,
    'username': 'reply@shoutit.com',
    'password': 'replytomenow',
    'use_tls': True,
    'time_out': 5,
    'backend': 'django.core.mail.backends.smtp.EmailBackend'
}

MANDRILL_SMTP = {
    'default_from_email': 'Shoutit <noreply@shoutit.com>',
    'host': 'smtp.mandrillapp.com',
    'port': 587,
    'username': 'info@shoutit.com',
    'password': 'bneGVmK5BHC5B9pyLUEj_w',
    'use_tls': True,
    'time_out': 5,
    'backend': 'django.core.mail.backends.smtp.EmailBackend'
}

FILE_SMTP = {
    'host': 'localhost',
    'backend': 'django.core.mail.backends.filebased.EmailBackend',
    'file_path': os.path.join(LOG_DIR, 'messages')
}

EMAIL_BACKENDS = {
    'google': GOOGLE_SMTP,
    'mandrill': MANDRILL_SMTP,
    'file': FILE_SMTP
}

if not LOCAL or FORCE_SMTP:
    EMAIL_USING = EMAIL_BACKENDS['mandrill']
else:
    EMAIL_USING = EMAIL_BACKENDS['file']

DEFAULT_FROM_EMAIL = EMAIL_USING.get('default_from_email')
EMAIL_HOST = EMAIL_USING.get('host')
EMAIL_PORT = EMAIL_USING.get('port')
EMAIL_HOST_USER = EMAIL_USING.get('username')
EMAIL_HOST_PASSWORD = EMAIL_USING.get('password')
EMAIL_USE_TLS = EMAIL_USING.get('use_tls')
EMAIL_TIMEOUT = EMAIL_USING.get('time_out')
EMAIL_BACKEND = EMAIL_USING.get('backend')
EMAIL_FILE_PATH = EMAIL_USING.get('file_path')

info("FORCE_SMTP:", FORCE_SMTP)
info("EMAIL_HOST:", EMAIL_HOST)

# Facebook App
FACEBOOK_APP_ID = '353625811317277'
FACEBOOK_APP_SECRET = '75b9dadd2f876a405c5b4a9d4fc4811d'

# Google App
GOOGLE_API = {
    'CLIENTS': {
        'web': {'FILE': os.path.join(API_DIR, 'assets', 'googleapiclients', 'web.json')},
        'android': {'FILE': os.path.join(API_DIR, 'assets', 'googleapiclients', 'android.json')},
        'ios': {'FILE': os.path.join(API_DIR, 'assets', 'googleapiclients', 'ios.json')},
    }
}


# Filter
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

CLOUD_USERNAME = 'noorsyron'
CLOUD_API_KEY = '3528746c5ca336ee6be4f293fdb66a57'
CLOUD_IDENTITY = 'rackspace'
CLOUD_FILES_SERVICE_NET = False  # True
SHOUT_IMAGES_CDN = 'c296814.r14.cf1.rackcdn.com'

# PayPal and Payment
PAYPAL_IDENTITY_TOKEN = 't9KJDunfc1X12lnPenlifnxutxvYiUOeA1PfPy6g-xpqHs5WCXA7V7kgqXO'  # 'SeS-TUDO3rKFsAIXxQOs6bjn1_RVrqBJE8RaQ7hmozmkXBuNnFlFAhf7jJO'
PAYPAL_RECEIVER_EMAIL = 'nour@syrex.me'
PAYPAL_PRIVATE_CERT = os.path.join(API_DIR, 'assets', 'certificates', 'paypal',
                                   'paypal-private-key.pem')
PAYPAL_PUBLIC_CERT = os.path.join(API_DIR, 'assets', 'certificates', 'paypal',
                                  'paypal-public-key.pem')
PAYPAL_CERT = os.path.join(API_DIR, 'assets', 'certificates', 'paypal', 'paypal-cert.pem')
PAYPAL_CERT_ID = '5E7VKRU5XWGMJ'
PAYPAL_NOTIFY_URL = 'http://80.227.53.34/paypal_ipn/'
PAYPAL_RETURN_URL = 'http://80.227.53.34/paypal_return/'
PAYPAL_CANCEL_URL = 'http://80.227.53.34/paypal_cancel/'

PAYPAL_SUBSCRIPTION_RETURN_URL = 'http://80.227.53.34/bsignup/'
PAYPAL_SUBSCRIPTION_CANCEL_URL = 'http://80.227.53.34/bsignup/'

PAYPAL_BUSINESS = 'biz_1339997492_biz@syrex.me'
PAYPAL_TEST = True

SUBSCRIPTION_PAYPAL_SETTINGS = {
    'notify_url': PAYPAL_NOTIFY_URL,
    'return': PAYPAL_RETURN_URL,
    'cancel_return': PAYPAL_CANCEL_URL,
    'business': PAYPAL_BUSINESS,
}

SUBSCRIPTION_PAYPAL_FORM = 'paypal.standard.forms.PayPalEncryptedPaymentsForm'

CPSP_ID = 'syrexme'
CPSP_PASS_PHRASE = '$Yr3x_PassPhrase#'

# Rest FW
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'shoutit.api.versioning.ShoutitNamespaceVersioning',
    'DEFAULT_VERSION': 'v2',
    'ALLOWED_VERSIONS': ['v2'],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework_oauth.authentication.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'shoutit.api.v2.permissions.IsSecure',
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'shoutit.api.v2.renderers.ShoutitBrowsableAPIRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': [],
    'URL_FIELD_NAME': 'api_url',
}

ENFORCE_SECURE = PROD and not DEBUG

# oauth2 settings
OAUTH_SINGLE_ACCESS_TOKEN = True
OAUTH_ENFORCE_SECURE = PROD and not DEBUG
OAUTH_ENFORCE_CLIENT_SECURE = True
OAUTH_DELETE_EXPIRED = True

SWAGGER_SETTINGS = {
    'exclude_namespaces': [],
    'api_version': '2.0',
    'api_path': '/',
    'protocol': 'https' if PROD else 'http',
    'enabled_methods': [
        'get',
        'post',
        'put',
        'patch',
        'delete',
    ],
    'api_key': '',
    # 'is_authenticated': True,
    # 'is_superuser': True,
    'permission_denied_handler': None,
    'info': {
        # 'contact': 'mo.chawich@gmail.com',
        'description': '',
        'title': 'Shoutit API V2 Documentation',
    },
    'doc_expansion': 'none',
}

# some monkey patching for global imports
from common import monkey_patches

info('Monkeys: Loaded')
info("==================================================")
