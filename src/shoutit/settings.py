# -*- coding: utf-8 -*-
"""

"""
import os
import sys
from datetime import timedelta

from django.utils.translation import ugettext_lazy as _

from common.utils import strtobool, info
from config import load_env

"""
=================================
        Environment
=================================
"""
SRC_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
API_DIR = os.path.dirname(SRC_DIR)
SHOUTIT_ENV = os.environ.get('SHOUTIT_ENV', 'development')

# Read env variables from .env file based on `SHOUTIT_ENV`
load_env(env_name=SHOUTIT_ENV)

with open(os.path.join(API_DIR, 'BUILD_NUM')) as f:
    BUILD_NUM = f.read()
with open(os.path.join(API_DIR, 'VERSION')) as f:
    VERSION = f.read()

"""
=================================
        Connection
=================================
"""
WSGI_APPLICATION = 'wsgi.application'
ALLOWED_HOSTS = ['127.0.0.1', '.shoutit.com']
INTERNAL_IPS = ['127.0.0.1']
GUNICORN = 'gunicorn' in os.environ.get('SERVER_SOFTWARE', '')

# URLs
ROOT_URLCONF = 'shoutit.urls'
APPEND_SLASH = False
API_LINK = os.environ.get('API_LINK')
SITE_LINK = os.environ.get('SITE_LINK')
APP_LINK_SCHEMA = os.environ.get('APP_LINK_SCHEMA')

# Security
DEBUG = strtobool(os.environ.get('SHOUTIT_DEBUG'))
SECRET_KEY = os.environ.get('SECRET_KEY')
ENFORCE_SECURE = not DEBUG
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Admin
ADMINS = (
    ('Mo Chawich', 'mo.chawich@shoutit.com'),
)
MANAGERS = ADMINS
GRAPPELLI_ADMIN_TITLE = 'Shoutit API Admin'

"""
=================================
        Shoutit defaults
=================================
"""
AUTH_USER_MODEL = 'shoutit.User'
MAX_EXPIRY_DAYS = 60
MAX_EXPIRY_DAYS_SSS = 30
NEARBY_CITIES_RADIUS_KM = 65
MAX_IMAGES_PER_ITEM = 10
MAX_VIDEOS_PER_ITEM = 2
SHOUT_EXPIRY_NOTIFY = 2
FORCE_SSS_NOTIFY = False
USER_LAST_LOGIN_EXPIRY_SECONDS = 60 * 60
"""
=================================
            Elasticsearch
=================================
"""
ES_HOST = os.environ.get('ES_HOST')
ES_PORT = os.environ.get('ES_PORT')
if ES_PORT and 'tcp' in ES_PORT:
    ES_PORT = ES_PORT.split(':')[-1]
ES_URL = f"{ES_HOST}:{ES_PORT}"
ES_BASE_INDEX = os.environ.get('ES_BASE_INDEX')

"""
=================================
            Caching
=================================
"""
REDIS_HOST = os.environ.get('REDIS_HOST')
REDIS_PORT = os.environ.get('REDIS_PORT')
if REDIS_PORT and 'tcp' in REDIS_PORT:
    REDIS_PORT = REDIS_PORT.split(':')[-1]


def default_redis_conf(db=0):
    return {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/{db}",
        'TIMEOUT': None,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }


SESSION_CACHE_ALIAS = "session"
WORKER_CACHE_ALIAS = "worker"
WORKER_MAIL_CACHE_ALIAS = "worker_mail"
WORKER_PUSH_CACHE_ALIAS = "worker_push"
WORKER_PUSHER_CACHE_ALIAS = "worker_pusher"
WORKER_CREDIT_CACHE_ALIAS = "worker_credit"
WORKER_PUSH_BROADCAST_CACHE_ALIAS = "worker_push_broadcast"
WORKER_SSS_CACHE_ALIAS = "worker_sss"

CACHES = {
    "default": default_redis_conf(1),
    SESSION_CACHE_ALIAS: default_redis_conf(2),
    WORKER_CACHE_ALIAS: default_redis_conf(3),
    WORKER_MAIL_CACHE_ALIAS: default_redis_conf(4),
    WORKER_PUSH_CACHE_ALIAS: default_redis_conf(5),
    WORKER_PUSHER_CACHE_ALIAS: default_redis_conf(6),
    WORKER_CREDIT_CACHE_ALIAS: default_redis_conf(7),
    WORKER_PUSH_BROADCAST_CACHE_ALIAS: default_redis_conf(14),
    WORKER_SSS_CACHE_ALIAS: default_redis_conf(15),
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

"""
=================================
           Queuing
=================================
"""
FORCE_SYNC_RQ = strtobool(os.environ.get('FORCE_SYNC_RQ'))
RQ_QUEUE = 'default'
RQ_QUEUE_MAIL = 'mail'
RQ_QUEUE_PUSH = 'push'
RQ_QUEUE_PUSHER = 'pusher'
RQ_QUEUE_CREDIT = 'credit'
RQ_QUEUE_PUSH_BROADCAST = 'push_broadcast'
RQ_QUEUE_SSS = 'sss'
RQ_QUEUES = {
    RQ_QUEUE: {
        'USE_REDIS_CACHE': WORKER_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 30,
    },
    RQ_QUEUE_MAIL: {
        'USE_REDIS_CACHE': WORKER_MAIL_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 10,
    },
    RQ_QUEUE_PUSH: {
        'USE_REDIS_CACHE': WORKER_PUSH_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 10,
    },
    RQ_QUEUE_PUSHER: {
        'USE_REDIS_CACHE': WORKER_PUSHER_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 10,
    },
    RQ_QUEUE_CREDIT: {
        'USE_REDIS_CACHE': WORKER_CREDIT_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 10,
    },
    RQ_QUEUE_PUSH_BROADCAST: {
        'USE_REDIS_CACHE': WORKER_PUSH_BROADCAST_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 30,
    },
    RQ_QUEUE_SSS: {
        'USE_REDIS_CACHE': WORKER_SSS_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 30,
    },
}
if FORCE_SYNC_RQ:
    for queue_config in RQ_QUEUES.values():
        queue_config['ASYNC'] = False

"""
=================================
       Application definition
=================================
"""
INSTALLED_APPS = [
    'grappelli',
    'mptt',
    'django_mptt_admin',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.postgres',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_swagger',
    'provider',
    'provider.oauth2',
    'push_notifications',
    'django_rq',
    'corsheaders',
    'heartbeat',
    'raven.contrib.django.raven_compat',

    'shoutit',
    'shoutit_credit',
    'shoutit_crm',
    'shoutit_pusher',
    'shoutit_twilio',
    'hvad',
]

TWILIO_ENV = os.environ.get('TWILIO_ENV', SHOUTIT_ENV)
PUSHER_ENV = os.environ.get('PUSHER_ENV', SHOUTIT_ENV)

"""
=================================
       Middleware
=================================
"""
REQUEST_ID_HEADER = None
CORS_ORIGIN_ALLOW_ALL = True
MIDDLEWARE_CLASSES = [
    'shoutit.middleware.AgentMiddleware',
    'shoutit.middleware.XForwardedForMiddleware',
    'request_id.middleware.RequestIdMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Shoutit Custom Middleware
    # 'shoutit.middleware.UserPermissionsMiddleware',
    'shoutit.middleware.UserAttributesMiddleware',
    'shoutit.middleware.FBMiddleware',
    'shoutit.middleware.BadRequestsMiddleware',
    'shoutit.api.exceptions.APIExceptionMiddleware',
    # 'common.middleware.ProfilerMiddleware.ProfileMiddleware',
    # 'common.middleware.SqlLogMiddleware.SQLLogToConsoleMiddleware',
]

"""
=================================
            Database
=================================
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}

"""
=================================
       Internationalization
=================================
"""
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = False
USE_TZ = True
LANGUAGES = (
    ('en', _('English')),
    ('ar', _('Arabic')),
    ('de', _('German')),
    ('es', _('Spanish')),
    ('zh', _('Chinese')),
)
DEFAULT_LANGUAGE_CODE = 'en'
LOCALE_PATHS = (
    os.path.join(SRC_DIR, 'locale'),
)

"""
=================================
         Static files
=================================
"""
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    INSTALLED_APPS += (
        'storages',
    )
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = 'shoutit-api-static'
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
    STATIC_URL = "https://%s/" % AWS_S3_CUSTOM_DOMAIN
else:
    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(API_DIR, 'static')
    if not os.path.exists(STATIC_ROOT):
        os.makedirs(STATIC_ROOT)

# Templates
TEMPLATE_DEBUG = DEBUG
TEMPLATE_DIRS = (
    os.path.join(SRC_DIR, 'templates'),
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

"""
=================================
            Services
=================================
"""
# Push
# Both certificates used for development(by AppUnite) and production (by Shoutit) are considered `production` certificates
APNS_SANDBOX = strtobool(os.environ.get('APNS_SANDBOX'))
FORCE_PUSH = strtobool(os.environ.get('FORCE_PUSH'))
APNS_CERT_NAME = 'push-%s.pem' % SHOUTIT_ENV
APNS_CERT_FILE = os.path.join(SRC_DIR, 'assets', 'certificates', 'ios', APNS_CERT_NAME)
USE_PUSH = os.path.isfile(APNS_CERT_FILE)
PUSH_NOTIFICATIONS_SETTINGS = {
    'GCM_API_KEY': "AIzaSyBld5731YUMSNuLBO5Gu2L4Tsj-CrQZGIg",
    'APNS_CERTIFICATE': APNS_CERT_FILE,
    'APNS_HOST': "gateway.%spush.apple.com" % ('sandbox.' if APNS_SANDBOX else ''),
    'APNS_FEEDBACK_HOST': "feedback.%spush.apple.com" % ('sandbox.' if APNS_SANDBOX else '')
}
MAX_BROADCAST_RECIPIENTS = 1000

# Mixpanel
MIXPANEL_TOKEN = os.environ.get('MIXPANEL_TOKEN', '')
MIXPANEL_SECRET = os.environ.get('MIXPANEL_SECRET', '')
USE_MIXPANEL = MIXPANEL_TOKEN is not ''

# Nexmo
NEXMO_API_KEY = "7c650639"
NEXMO_API_SECRET = "4ee98397"

# IP2Location
IP2LOCATION_DB_BIN = os.path.join(API_DIR, 'meta', 'ip2location', 'IP2LOCATION-LITE-DB9.BIN')

# AntiCaptcha
ANTI_KEY = 'eb8e82bf16467103e8e0f49f6ea2924a'

"""
=================================
          Linked Apps
=================================
"""
# Facebook App
FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID')
FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET')

# Google App
GOOGLE_WEB_CLIENT = os.path.join(SRC_DIR, 'assets', 'google-web-client.json')

"""
=================================
            Mail
=================================
"""
LOG_DIR = os.path.join(API_DIR, 'log', 'shoutit-api-' + SHOUTIT_ENV)
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

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
SENDGRID_SMTP = {
    'default_from_email': 'Shoutit <noreply@shoutit.com>',
    'host': 'smtp.sendgrid.net',
    'port': 587,
    'username': 'shoutit-api',
    'password': 'tE$X@WdDL}4d:FAK',
    'use_tls': True,
    'time_out': 5,
    'backend': 'django.core.mail.backends.smtp.EmailBackend'
}
FILE_SMTP = {
    'default_from_email': 'Shoutit <noreply@shoutit.com>',
    'host': 'localhost',
    'backend': 'django.core.mail.backends.filebased.EmailBackend',
    'file_path': os.path.join(LOG_DIR, 'messages')
}
EMAIL_BACKENDS = {
    'google': GOOGLE_SMTP,
    'sendgrid': SENDGRID_SMTP,
    'file': FILE_SMTP
}
EMAIL_ENV = os.environ.get('EMAIL_ENV')
EMAIL_USING = EMAIL_BACKENDS[EMAIL_ENV]
DEFAULT_FROM_EMAIL = EMAIL_USING.get('default_from_email')
EMAIL_HOST = EMAIL_USING.get('host')
EMAIL_PORT = EMAIL_USING.get('port')
EMAIL_HOST_USER = EMAIL_USING.get('username')
EMAIL_HOST_PASSWORD = EMAIL_USING.get('password')
EMAIL_USE_TLS = EMAIL_USING.get('use_tls')
EMAIL_TIMEOUT = EMAIL_USING.get('time_out')
EMAIL_BACKEND = EMAIL_USING.get('backend')
EMAIL_FILE_PATH = EMAIL_USING.get('file_path')

"""
=================================
              DRF
=================================
"""
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'shoutit.api.versioning.ShoutitNamespaceVersioning',
    'DEFAULT_VERSION': 'v3',
    'ALLOWED_VERSIONS': ['v2', 'v3'],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'shoutit.api.authentication.ShoutitTokenAuthentication',
        'shoutit.api.authentication.ShoutitOAuth2Authentication',
        'shoutit.api.authentication.ShoutitSessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'shoutit.api.permissions.IsSecure',
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'shoutit.api.parsers.ShoutitJSONParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'shoutit.api.renderers.ShoutitBrowsableAPIRenderer',
    ),
    'EXCEPTION_HANDLER': 'shoutit.api.exceptions.exception_handler',
    'DEFAULT_FILTER_BACKENDS': [],
    'URL_FIELD_NAME': 'api_url',
}
DEFAULT_MAX_PAGE_SIZE = 30
CACHE_CONTROL_MAX_AGE = 60 * 5

REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_CACHE_RESPONSE_TIMEOUT': CACHE_CONTROL_MAX_AGE,
    'DEFAULT_CACHE_ERRORS': False,
    'DEFAULT_CACHE_KEY_FUNC': 'shoutit.api.cache.shoutit_default_cache_key_func',
}

# OAuth2 settings
OAUTH_SINGLE_ACCESS_TOKEN = True
OAUTH_ENFORCE_SECURE = ENFORCE_SECURE
OAUTH_ENFORCE_CLIENT_SECURE = True
OAUTH_DELETE_EXPIRED = True
OAUTH_EXPIRE_DELTA = timedelta(days=365)

SWAGGER_SETTINGS = {
    'api_version': '3',
    'api_path': '/',
    'enabled_methods': [
        'get',
        'post',
        'patch',
        'delete',
    ],
    'exclude_namespaces': ['v2'],
    'api_key': '',
    # 'is_authenticated': True,
    'is_superuser': False,
    'permission_denied_handler': None,
    'info': {
        'contact': 'mo.chawich@shoutit.com',
        'description': '',
        'title': 'Shoutit API Documentation',
    },
    'doc_expansion': 'none',
}

"""
=================================
             Logging
=================================
"""
RAVEN_CONFIG = {
    'build': BUILD_NUM,
    'dsn': os.environ.get('RAVEN_DSN', ''),
    'environment': SHOUTIT_ENV,
    'release': VERSION,
    'string_max_length': 1000,
    'transport': 'raven.transport.threaded_requests.ThreadedRequestsHTTPTransport',
}
USE_SENTRY = RAVEN_CONFIG['dsn'] is not ''
SENTRY_CLIENT = 'shoutit.api.exceptions.ShoutitRavenClient'

# Disable Sentry while on development or when running py.test
if DEBUG and not USE_SENTRY:
    INSTALLED_APPS.remove('raven.contrib.django.raven_compat')

LOG_SQL = False

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s'
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
        'use_sentry': {
            '()': 'common.log.UseSentry',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
            'formatter': 'simple'
        },
        'console_err': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
            'formatter': 'simple'
        },
        'console_out': {
            'level': 'DEBUG' if LOG_SQL else 'INFO',
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
            'formatter': 'simple',
            'filters': ['require_debug_true'],
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.handlers.SentryHandler',
            'filters': ['use_sentry'],
        },
        'sentry_all': {
            'level': 'DEBUG',
            'class': 'raven.contrib.django.handlers.SentryHandler',
            'filters': ['use_sentry'],
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
        'sss_file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'filename': os.path.join(LOG_DIR, 'sss.log'),
            'formatter': 'simple_dashed'
        },
        'null': {
            "class": 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console_out', 'console_err', 'sentry'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
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
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'handlers': ['console_out', 'console_err', 'sentry'],
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
        'elasticsearch': {
            'handlers': ['console_out', 'console_err', 'sentry'],
            'level': 'WARNING',
            'propagate': False
        },
        '': {
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'handlers': ['console_out', 'console_err', 'sentry'],
        },
    }
}

info("==================================================")
info("================== Shoutit API ===================")
info("==================================================")
info("VERSION:", VERSION)
info("BUILD_NUM:", BUILD_NUM)
info("SHOUTIT_ENV:", SHOUTIT_ENV)
info("GUNICORN:", GUNICORN)
info("DEBUG:", DEBUG)
info("USE_SENTRY:", USE_SENTRY, RAVEN_CONFIG['dsn'][-5:])
info("==================================================")
info("API_LINK:", API_LINK)
info("SITE_LINK:", SITE_LINK)
info("APP_LINK_SCHEMA:", APP_LINK_SCHEMA)
info("==================================================")
info("DB_HOST:DB_PORT:", f"{DATABASES['default']['HOST']}:{DATABASES['default']['PORT']}")
info("REDIS_HOST:REDIS_PORT:", f'{REDIS_HOST}:{REDIS_PORT}')
info("ES_HOST:ES_PORT:", f'{ES_HOST}:{ES_PORT}')
info("FORCE_SYNC_RQ:", FORCE_SYNC_RQ)
info("==================================================")
info('STATIC_URL:', STATIC_URL)
info("==================================================")
info("EMAIL_ENV:", EMAIL_ENV)
info('USE_PUSH:', USE_PUSH)
info('PUSHER_ENV:', PUSHER_ENV)
info('TWILIO_ENV:', TWILIO_ENV)
info("==================================================")
