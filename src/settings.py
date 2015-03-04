# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, print_function

import os
import sys


def info(*args):
    print("[INFO]  ", *args, file=sys.stderr)

# include the BACKEND_DIR in sys.path a.k.a PYTHONPATH to be able to use etc.env_settings for example.
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from etc.env_settings import *
from common.utils import get_address_port, check_offline_mood

OFFLINE_MODE = check_offline_mood()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/
SECRET_KEY = '0af3^t(o@8cl(8z_gli1@)j*)&(&qzlvu7gox@koj-e#u8z*$q'

# using gunicorn or not
GUNICORN = 'SERVER_SOFTWARE' in os.environ and 'gunicorn' in os.environ.get('SERVER_SOFTWARE')
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

elif DEV:
    DEBUG = True
    SHOUT_IT_DOMAIN = 'dev.shoutit.com'
    SHOUT_IT_HOST = 'dev.shoutit.com'

else:  # LOCAL
    DEBUG = True
    SHOUT_IT_DOMAIN = 'shoutit.dev:8000'
    SHOUT_IT_HOST = 'shoutit.dev'

info("DEBUG:", DEBUG)


# URLs
ROOT_URLCONF = 'urls'
APPEND_SLASH = False
IS_SITE_SECURE = PROD
SCHEME = 'https' if IS_SITE_SECURE else 'http'
SITE_LINK = '%s://%s/' % (SCHEME, SHOUT_IT_DOMAIN)
WSGI_APPLICATION = 'wsgi.application'

info("SITE_LINK:", SITE_LINK)

USE_X_FORWARDED_HOST = True

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
SHOUT_EXPIRY_NOTIFY = 2
MAX_EXPIRY_DAYS = 30
ACCOUNT_ACTIVATION_DAYS = 7

RANK_COEFFICIENT_TIME = 0.7  # value should be between 0.0 ~ 1.0
RANK_COEFFICIENT_FOLLOW = 0.014  # value should be between 0.0 ~ 1.0
RANK_COEFFICIENT_DISTANCE = 1  # value should be between 0.0 ~ 1.0


# Redis
SESSION_REDIS_HOST = 'localhost'
SESSION_REDIS_PORT = 6379
REDIS_SOCKET_TIMEOUT = 30
SESSION_REDIS_DB = 0
SESSION_REDIS_PASSWORD = 'password'
SESSION_REDIS_PREFIX = 'session'

# to access session from JS, needed for realtime
SESSION_COOKIE_HTTPONLY = False

# Caching
DEV_SESSION_ENGINE = 'django.contrib.sessions.backends.db'
DEV_CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 240
    }
}
REDIS_SESSION_ENGINE = 'redis_sessions.session'
REDIS_CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'TIMEOUT': 12 * 60 * 60
    }
}

SESSION_ENGINE = DEV_SESSION_ENGINE
CACHES = DEV_CACHES

AUTH_USER_MODEL = 'shoutit.User'

# Application definition

INSTALLED_APPS = (
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'push_notifications',
    # 'paypal.standard.ipn',
    # 'paypal.standard.pdt',
    # 'keyedcache',
    # 'livesettings',
    # 'l10n',
    # 'payment',
    # 'subscription',
    'shoutit',

    'provider',
    'provider.oauth2',

    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_swagger',
)
# apps only on local development
if LOCAL:
    INSTALLED_APPS += (
        'django_extensions',
        'storages',
    )
# apps only on server development
if DEV:
    INSTALLED_APPS += (
    )
# apps only on production
if PROD:
    INSTALLED_APPS += (
    )
# apps when gunicorn is on
if GUNICORN:
    INSTALLED_APPS += (
    )

RAVEN_CONFIG = {
    'dsn': 'https://b26adb7e1a3b46dabc1b05bc8355008d:b820883c74724dcb93753af31cb21ee4@app.getsentry.com/36984',
}

APNS_SANDBOX = False
PUSH_NOTIFICATIONS_SETTINGS = {
    'GCM_API_KEY': "AIzaSyBld5731YUMSNuLBO5Gu2L4Tsj-CrQZGIg",
    'APNS_CERTIFICATE': os.path.join(BACKEND_DIR, 'assets', 'certificates', 'ios', 'push-%s.pem'
                                     % ('dev' if APNS_SANDBOX else 'prod')),
    'APNS_HOST': "gateway.%spush.apple.com" % ('sandbox.' if APNS_SANDBOX else ''),
    'APNS_FEEDBACK_HOST': "feedback.%spush.apple.com" % ('sandbox.' if APNS_SANDBOX else '')
}
info('APNS_SANDBOX:', APNS_SANDBOX)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
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
        'NAME': ENV,
        'USER': 'syron',
        'PASSWORD': '123',
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

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

# todo: AWS
# todo: no more static files needed after web app is ready
if False:
    AWS_STORAGE_BUCKET_NAME = 'man-static'
    AWS_ACCESS_KEY_ID = 'AKIAJ7YQGDWLJVDUE3SA'
    AWS_SECRET_ACCESS_KEY = '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'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    STATIC_URL = "https://%s/" % AWS_S3_CUSTOM_DOMAIN
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
else:
    STATIC_URL = '/static/'

MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(ENV_DIR, 'static')
MEDIA_ROOT = os.path.join(ENV_DIR, 'media')

STATICFILES_DIRS = (
    os.path.join(DJANGO_DIR, 'static'),
)

# Templates
TEMPLATE_DIRS = (
    os.path.join(DJANGO_DIR, 'templates', 'site'),
    os.path.join(DJANGO_DIR, 'templates', 'ajax_templates'),
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
            'format': '%(levelname)s %(message)s'
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
        },
        'console_err': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
        },
        'console_out': {
            'level': 'DEBUG' if LOCAL and LOG_SQL else 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'filters': ['level_below_warning'],
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
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
        '': {
            'handlers': ['console_out', 'console_err', 'sentry'],
        },
        # 'requests': {
        # 'level': 'DEBUG',
        #     'handlers': ['console_out', 'console_err', 'sentry'],
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
    }
}

# Mail Settings
SERVER_EMAIL = 'Shoutit <info@shoutit.com>'
USE_GOOGLE = False
USE_MANDRILL = False

if USE_GOOGLE:
    DEFAULT_FROM_EMAIL = 'Nour <nour@syrex.me>'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = '587'
    EMAIL_HOST_USER = 'nour@syrex.me'
    EMAIL_HOST_PASSWORD = ''
    EMAIL_USE_TLS = True
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

elif USE_MANDRILL:
    DEFAULT_FROM_EMAIL = 'Shoutit <info@shoutit.com>'
    EMAIL_HOST = 'smtp.mandrillapp.com'
    EMAIL_PORT = '587'
    # EMAIL_HOST_USER = 'noor.syron@gmail.com'
    # EMAIL_HOST_PASSWORD = 'xb-lOrXsVGILf91XsS0hgw'
    EMAIL_HOST_USER = 'nour@syrex.com'
    EMAIL_HOST_PASSWORD = 'bneGVmK5BHC5B9pyLUEj_w'
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = True
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    DEFAULT_FROM_EMAIL = 'Shoutit <info@shoutit.com>'
    EMAIL_HOST = SHOUT_IT_HOST
    EMAIL_PORT = '25'
    EMAIL_HOST_USER = 'admin'
    EMAIL_HOST_PASSWORD = 'password'
    EMAIL_USE_TLS = False
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = os.path.join(LOG_DIR, 'messages')

info("EMAIL_HOST:", EMAIL_HOST)

# Auth Settings
LOGIN_URL = '/signin/'
LOGIN_URL_MODAL = '/#signin/'
LOGOUT_URL = '/signout/'
ACTIVATE_URL = '/activate/'
ACTIVATE_URL_MODAL = '/#activate/'

# Facebook App
FACEBOOK_APP_ID = '353625811317277'
FACEBOOK_APP_SECRET = '75b9dadd2f876a405c5b4a9d4fc4811d'

# Google App
GOOGLE_API = {
    'CLIENTS': {
        'web': {'FILE': os.path.join(BACKEND_DIR, 'assets', 'googleapiclients', 'web.json')},
        'android': {'FILE': os.path.join(BACKEND_DIR, 'assets', 'googleapiclients', 'android.json')},
        'ios': {'FILE': os.path.join(BACKEND_DIR, 'assets', 'googleapiclients', 'ios.json')},
    }
}


# Contact Import
CONTACT_IMPORT_SETTINGS = {
    'google': {'consumer_key': '572868510623.apps.googleusercontent.com', 'consumer_secret': 'GkQnvuCaAzgdIn6V1wZ70DW8'},
    'yahoo': {
        'consumer_key': 'dj0yJmk9akptTldFWW1qd1F1JmQ9WVdrOWVWZzRkbTVGTmpJbWNHbzlOak13T0RNNU5qSS0mcz1jb25zdW1lcnNlY3JldCZ4PTE2',
        'consumer_secret': 'c3d0cd060d1085000f7b5d1698f2c9e65632a4e6'
    },
    'hotmail': {
        'consumer_key': '00000000480C4181',
        'consumer_secret': 'XpebWKeFBR28I4JV9vAsJjg85gAIqASk',
        'policy_url': 'https://www.shoutit.com/privacy/?lang=en'
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
PAYPAL_PRIVATE_CERT = os.path.join(BACKEND_DIR, 'assets', 'certificates', 'paypal', 'paypal-private-key.pem')
PAYPAL_PUBLIC_CERT = os.path.join(BACKEND_DIR, 'assets', 'certificates', 'paypal', 'paypal-public-key.pem')
PAYPAL_CERT = os.path.join(BACKEND_DIR, 'assets', 'certificates', 'paypal', 'paypal-cert.pem')
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
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'shoutit.api.v2.renderers.ShoutitBrowsableAPIRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': [],
    'PAGINATE_BY': 10,
    'PAGINATE_BY_PARAM': 'page_size',
    'MAX_PAGINATE_BY': 100,
    'URL_FIELD_NAME': 'api_url',
}

# oauth2 settings
OAUTH_SINGLE_ACCESS_TOKEN = True
ENFORCE_SECURE = False
ENFORCE_CLIENT_SECURE = True
DELETE_EXPIRED = True

SWAGGER_SETTINGS = {
    'exclude_namespaces': [],
    'api_version': '2.0',
    'api_path': '/',
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
