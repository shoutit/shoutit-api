"""
Django settings for shoutit project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

import sys
import PIL.Image
sys.modules['Image'] = PIL.Image

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '0af3^t(o@8cl(8z_gli1@)j*)&(&qzlvu7gox@koj-e#u8z*$q'

# Prod or Dev
DEV = False if os.environ.get('HOME') == '/root' else True
if DEV:
    DEBUG = True
    SHOUT_IT_DOMAIN = 'shoutit.syrex:8000'
    SHOUT_IT_HOST = '127.0.0.1'
else:
    DEBUG = True
    SHOUT_IT_DOMAIN = 'www.shoutit.com'
    SHOUT_IT_HOST = 'shoutit.com'

TEMPLATE_DEBUG = DEBUG
ALLOWED_HOSTS = ['127.0.0.1', 'shoutit.syrex', 'shoutit.com']
INTERNAL_IPS = ('127.0.0.1', 'shoutit.syrex')
ADMINS = (
     ('Your Name', 'your_email@example.com'),
)
MANAGERS = ADMINS


# Shoutit defaults
MAX_REG_DAYS = 14
MAX_SHOUTS_INACTIVE_USER = 5
MAX_EXPIRY_DAYS_SSS = 7
SHOUT_EXPIRY_NOTIFY = 2
MAX_EXPIRY_DAYS = 14
ACCOUNT_ACTIVATION_DAYS = 7

RANK_COEFFICIENT_TIME = 0.7  # value should be between 0.0 ~ 1.0
RANK_COEFFICIENT_FOLLOW = 0.014  # value should be between 0.0 ~ 1.0
RANK_COEFFICIENT_DISTANCE = 1  # value should be between 0.0 ~ 1.0

# Celery Settings
BROKER_HOST = 'localhost'
BROKER_PORT = 5672
#BROKER_USER = "celery"
#BROKER_PASSWORD = "celery"
#BROKER_VHOST = "celery_host"
CELERY_RESULT_BACKEND = "amqp"
#CELERY_TASK_SERIALIZER = "json"
CELERY_IMPORTS = ("celery_tasks", )
#djcelery.setup_loader()

# Realtime and Redis
REALTIME_SERVER_URL = 'http://' + SHOUT_IT_HOST + ':7772/'  # 'www.shoutit.com'
REALTIME_SERVER_ADDRESS = SHOUT_IT_HOST
REALTIME_SERVER_TCP_PORT = 7771
REALTIME_SERVER_HTTP_PORT = 7772
REALTIME_SERVER_API_PORT = 7773
RABBIT_MQ_HOST = SHOUT_IT_HOST
RABBIT_MQ_PORT = 5672

SESSION_REDIS_HOST = 'localhost'
SESSION_REDIS_PORT = 6379
REDIS_SOCKET_TIMEOUT = 30
SESSION_REDIS_DB = 0
SESSION_REDIS_PASSWORD = 'password'
SESSION_REDIS_PREFIX = 'session'

# Caching
DEV_SESSION_ENGINE = 'django.contrib.sessions.backends.db'
DEV_CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'TIMEOUT': 240,
        }
}
REDIS_SESSION_ENGINE = 'redis_sessions.session'
REDIS_CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'TIMEOUT': 12 * 60 * 60,
    }
}
if DEV:
    redis = ''
    SESSION_ENGINE = DEV_SESSION_ENGINE
    CACHES = DEV_CACHES
else:
    try:
        import redis
        SESSION_ENGINE = REDIS_SESSION_ENGINE
        CACHES = REDIS_CACHES
    except ImportError:
        redis = ''
        SESSION_ENGINE = DEV_SESSION_ENGINE
        CACHES = DEV_CACHES

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'grappelli',
    'django.contrib.auth',
    'django.contrib.admindocs',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.ActivityLogger',
    'apps.shoutit',
    'widget_tweaks',
    'piston',
    'django_mobile',
    'djcelery',
    'djcelery_email',

    #'paypal.standard.ipn',
    #'paypal.standard.pdt',
    #'keyedcache',
    #'livesettings',
    #'l10n',
    #'sorl.thumbnail',
    #'product',
    #'product.modules.subscription',
    #'payment',
    #'satchmo_utils',
    #'app_plugins',
    #'subscription',
    #'debug_toolbar',
)
# apps only on development
if DEV:
    INSTALLED_APPS += (
    )
# apps only on production
else:
    INSTALLED_APPS += (
    )

MIDDLEWARE_CLASSES = (
    #'common.middleware.SqlLogMiddleware.SQLLogToConsoleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    # Shoutit Custom Middleware
    'apps.shoutit.middleware.SetLanguageMiddleware',
    'apps.shoutit.middleware.UserPermissionsMiddleware',
    'apps.shoutit.middleware.UserLocationMiddleware',
    'apps.shoutit.middleware.FBMiddleware',
    #'apps.ActivityLogger.middleware.ActivityLogger',
    #'common.middleware.ProfilerMiddleware.ProfileMiddleware',

    #'debug_toolbar.middleware.DebugToolbarMiddleware',

    'django_mobile.middleware.MobileDetectionMiddleware',
    'django_mobile.middleware.SetFlavourMiddleware',
)

# URLs
ROOT_URLCONF = 'apps.shoutit.urls'
APPEND_SLASH = True
IS_SITE_SECURE = False  # True

WSGI_APPLICATION = 'apps.shoutit.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

#DATABASES = {
#	'default': {
#		'ENGINE': 'django.db.backends.sqlite3',
#		'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#	}
#}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'shoutdb',                      # Or path to database file if using sqlite3.
        'USER': 'syron',                      # Not used with sqlite3.
        'PASSWORD': '123',                  # Not used with sqlite3.
        'HOST': 'localhost',
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
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
    #('ar', ugettext('Arabic')),
)
DEFAULT_LANGUAGE_CODE = 'en'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = '/opt/myenv/shoutit/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = '/opt/myenv/shoutit/media/'


# Templates
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'apps', 'shoutit', 'templates'),
    os.path.join(BASE_DIR, 'apps', 'shoutit', 'ajax_templates'),
    os.path.join(BASE_DIR, 'apps', 'shoutit', 'text_messages'),
    os.path.join(BASE_DIR, 'apps', 'shoutit', 'html_messages'),
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
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
        'message_only': {
            'format': '%(message)s'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'sql_file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'filename': os.path.join(BASE_DIR, 'logs', 'sql.log'),
        },
        'sql_console': {
            'level':'INFO',
            'class':'logging.StreamHandler',
            'formatter': 'message_only'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'SqlLogMiddleware' : {
            'handlers': ['sql_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'SqlLogMiddleware_console' : {
            'handlers': ['sql_console'],
            'level': 'INFO',
            'propagate': False,
        }
    }
}

# Mail Settings
if DEV:
    DEFAULT_FROM_EMAIL = 'ShoutIt <info@shoutit.com>'
    EMAIL_HOST = SHOUT_IT_HOST
    EMAIL_PORT = '25'
    EMAIL_HOST_USER = 'admin'
    EMAIL_HOST_PASSWORD = 'password'
    EMAIL_USE_TLS = False
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'messages')
else:
    DEFAULT_FROM_EMAIL = 'ShoutIt <info@shoutit.com>'
    EMAIL_HOST = SHOUT_IT_HOST
    EMAIL_PORT = '25'
    EMAIL_HOST_USER = 'admin'
    EMAIL_HOST_PASSWORD = 'password'
    EMAIL_USE_TLS = False
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'messages')
    #DEFAULT_FROM_EMAIL = 'Shoutit <noor.syron@gmail.com>'
    #EMAIL_HOST = 'smtp.gmail.com'
    #EMAIL_PORT = '587'
    #EMAIL_HOST_USER = 'noor.syron@gmail.com'
    #EMAIL_HOST_PASSWORD = 'Sni4hot*'
    #EMAIL_USE_TLS = True
    #EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
    SEND_GRID_SMTP_HOST = 'smtp.sendgrid.net'
    SEND_GRID_SMTP_USERNAME = 'shoutit'
    SEND_GRID_SMTP_PASSWORD = 'Syrex6me'


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
GOOGLE_APP_CLIENT_ID = '935842257865-s6069gqjq4bvpi4rcbjtdtn2kggrvi06.apps.googleusercontent.com'
GOOGLE_APP_CLIENT_SECRET = 'VzqpJcFV8C3X18qMKF50ogup'

# Contact Import
CONTACT_IMPORT_SETTINGS = {
    'google': { 'consumer_key': '572868510623.apps.googleusercontent.com', 'consumer_secret': 'GkQnvuCaAzgdIn6V1wZ70DW8' },
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

# SMS Service
SMS_SERVICE_WSDL_URL = 'https://www.smsglobal.com/mobileworks/soapserver.php?wsdl'
SMS_SERVICE_USERNAME = 'syrexme'
SMS_SERVICE_PASSWORD = '25600696'


# Filter
PROFANITIES_LIST = (
    'ass', 'ass lick', 'asses', 'asshole', 'assholes', 'asskisser', 'asswipe',
    'balls', 'bastard', 'beastial', 'beastiality', 'beastility', 'beaver',
    'belly whacker', 'bestial', 'bestiality', 'bitch', 'bitcher', 'bitchers',
    'bitches', 'bitchin', 'bitching', 'blow job', 'blowjob', 'blowjobs','bonehead',
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

## PayPal and Payment
CLOUD_USERNAME = 'noorsyron'
CLOUD_API_KEY = '3528746c5ca336ee6be4f293fdb66a57'
CLOUD_IDENTITY = 'rackspace'
CLOUD_FILES_SERVICE_NET = False # True
SHOUT_IMAGES_CDN = 'c296814.r14.cf1.rackcdn.com'

PAYPAL_IDENTITY_TOKEN = 't9KJDunfc1X12lnPenlifnxutxvYiUOeA1PfPy6g-xpqHs5WCXA7V7kgqXO' #'SeS-TUDO3rKFsAIXxQOs6bjn1_RVrqBJE8RaQ7hmozmkXBuNnFlFAhf7jJO'
PAYPAL_RECEIVER_EMAIL = 'nour@syrex.me'
PAYPAL_PRIVATE_CERT = os.path.join(BASE_DIR, 'apps', 'shoutit', 'static', 'Certificates', 'PayPal', 'paypal-private-key.pem')
PAYPAL_PUBLIC_CERT = os.path.join(BASE_DIR, 'apps', 'shoutit', 'static', 'Certificates', 'PayPal', 'paypal-public-key.pem')
PAYPAL_CERT = os.path.join(BASE_DIR, 'apps', 'shoutit', 'static', 'Certificates', 'PayPal', 'paypal-cert.pem')
PAYPAL_CERT_ID = '5E7VKRU5XWGMJ'
PAYPAL_NOTIFY_URL = 'http://80.227.53.34/paypal_ipn/'
PAYPAL_RETURN_URL = 'http://80.227.53.34/paypal_return/'
PAYPAL_CANCEL_URL = 'http://80.227.53.34/paypal_cancel/'

PAYPAL_SUBSCRIPTION_RETURN_URL = 'http://80.227.53.34/bsignup/'
PAYPAL_SUBSCRIPTION_CANCEL_URL = 'http://80.227.53.34/bsignup/'

PAYPAL_BUSINESS = 'biz_1339997492_biz@syrex.me'
PAYPAL_TEST = True

SUBSCRIPTION_PAYPAL_SETTINGS = {
    'notify_url' : PAYPAL_NOTIFY_URL,
    'return' : PAYPAL_RETURN_URL,
    'cancel_return' : PAYPAL_CANCEL_URL,
    'business' : PAYPAL_BUSINESS,
}

SUBSCRIPTION_PAYPAL_FORM = 'paypal.standard.forms.PayPalEncryptedPaymentsForm'

CPSP_ID = 'syrexme'
CPSP_PASS_PHRASE = '$Yr3x_PassPhrase#'

#SATCHMO_SETTINGS = {
#    'SHOP_BASE' : '',
#    'MULTISHOP' : True,
#}
