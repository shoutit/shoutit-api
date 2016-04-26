# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals, print_function
from settings_env import *  # NOQA
from common.utils import get_address_port
from django.utils.translation import ugettext_lazy as _

"""
=================================
        Connection
=================================
"""
WSGI_APPLICATION = 'wsgi.application'
ALLOWED_HOSTS = ['127.0.0.1', 'shoutit.dev', '.shoutit.com.', '.shoutit.com', '.dockerapp.io', '.dockerapp.io.',
                 'shoutit.ngrok.io']
INTERNAL_IPS = ('127.0.0.1', 'shoutit.dev')
GUNICORN = 'gunicorn' in os.environ.get('SERVER_SOFTWARE', '')
ADDRESS, PORT = get_address_port(GUNICORN)

# URLs
ROOT_URLCONF = 'shoutit.urls'
APPEND_SLASH = False
API_LINK = os.environ.get('API_LINK', 'http://shoutit.dev:8000/v3/')
SITE_LINK = os.environ.get('SITE_LINK', 'http://shoutit.dev:3000/')

# Security
if PROD:
    DEBUG = False
else:  # DEV and LOCAL
    DEBUG = os.environ.get('SHOUTIT_DEBUG', '').lower() == 'true'
SECRET_KEY = '0af3^t(o@8cl(8z_gli1@)j*)&(&qzlvu7gox@koj-e#u8z*$q'
ENFORCE_SECURE = PROD and not DEBUG
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Admin
ADMINS = (
    ('Mo Chawich', 'mo.chawich@gmail.com'),
)
MANAGERS = ADMINS
GRAPPELLI_ADMIN_TITLE = 'Shoutit'

"""
=================================
        Shoutit defaults
=================================
"""
AUTH_USER_MODEL = 'shoutit.User'
MAX_REG_DAYS = 14
MAX_SHOUTS_INACTIVE_USER = 5
MAX_EXPIRY_DAYS_SSS = 7
FORCE_SSS_NOTIFY = False
SHOUT_EXPIRY_NOTIFY = 2
MAX_EXPIRY_DAYS = 60
ACCOUNT_ACTIVATION_DAYS = 7
NEARBY_CITIES_RADIUS_KM = 65
MAX_IMAGES_PER_ITEM = 10
MAX_VIDEOS_PER_ITEM = 2

"""
=================================
            Elasticsearch
=================================
"""
ES_HOST = os.environ.get('ES_HOST', 'es.shoutit.com')
ES_PORT = os.environ.get('ES_PORT', '9200')
ES_URL = "%s:%s" % (ES_HOST, ES_PORT)
ES_BASE_INDEX = os.environ.get('ES_BASE_INDEX', 'shoutit_api_%s' % SHOUTIT_ENV)

"""
=================================
            Caching
=================================
"""
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis.shoutit.com')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')


def default_redis_conf(db=0):
    return {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://%s:%s/%s" % (REDIS_HOST, REDIS_PORT, str(db)),
        'TIMEOUT': None,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }


SESSION_CACHE_ALIAS = "session"
WORKER_CACHE_ALIAS = "worker"
WORKER_MAIL_CACHE_ALIAS = "worker_mail"
WORKER_PUSH_CACHE_ALIAS = "worker_push"
WORKER_PUSH_BROADCAST_CACHE_ALIAS = "worker_push_broadcast"
WORKER_PUSHER_CACHE_ALIAS = "worker_pusher"
WORKER_SSS_CACHE_ALIAS = "worker_sss"

CACHES = {
    "default": default_redis_conf(1),
    SESSION_CACHE_ALIAS: default_redis_conf(2),
    WORKER_CACHE_ALIAS: default_redis_conf(10),
    WORKER_MAIL_CACHE_ALIAS: default_redis_conf(11),
    WORKER_PUSH_CACHE_ALIAS: default_redis_conf(12),
    WORKER_PUSH_BROADCAST_CACHE_ALIAS: default_redis_conf(13),
    WORKER_PUSHER_CACHE_ALIAS: default_redis_conf(14),
    WORKER_SSS_CACHE_ALIAS: default_redis_conf(15),
}
SESSION_ENGINE = "django.contrib.sessions.backends.cache"

"""
=================================
           Queuing
=================================
"""
FORCE_SYNC_RQ = os.environ.get('FORCE_SYNC_RQ', False)
RQ_QUEUE = 'default'
RQ_QUEUE_MAIL = 'mail'
RQ_QUEUE_PUSH = 'push'
RQ_QUEUE_PUSH_BROADCAST = 'push_broadcast'
RQ_QUEUE_PUSHER = 'pusher'
RQ_QUEUE_SSS = 'sss'
RQ_QUEUES = {
    RQ_QUEUE: {
        'USE_REDIS_CACHE': WORKER_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 30,
    },
    RQ_QUEUE_MAIL: {
        'USE_REDIS_CACHE': WORKER_MAIL_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 30,
    },
    RQ_QUEUE_PUSH: {
        'USE_REDIS_CACHE': WORKER_PUSH_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 5,
    },
    RQ_QUEUE_PUSH_BROADCAST: {
        'USE_REDIS_CACHE': WORKER_PUSH_BROADCAST_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 5,
    },
    RQ_QUEUE_PUSHER: {
        'USE_REDIS_CACHE': WORKER_PUSHER_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 5,
    },
    RQ_QUEUE_SSS: {
        'USE_REDIS_CACHE': WORKER_SSS_CACHE_ALIAS,
        'DEFAULT_TIMEOUT': 30,
    },
}
if DEBUG or FORCE_SYNC_RQ:
    for queue_config in RQ_QUEUES.itervalues():
        queue_config['ASYNC'] = False

"""
=================================
       Application definition
=================================
"""
INSTALLED_APPS = (
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

    'shoutit_twilio',
    'shoutit_pusher',
    'shoutit_crm',
    'shoutit',
)

TWILIO_ENV = os.environ.get('TWILIO_ENV', 'local')
PUSHER_ENV = os.environ.get('PUSHER_ENV', 'local')

"""
=================================
       Middleware
=================================
"""
REQUEST_ID_HEADER = None
CORS_ORIGIN_ALLOW_ALL = True
MIDDLEWARE_CLASSES = (
    'shoutit.middleware.XForwardedForMiddleware',
    'request_id.middleware.RequestIdMiddleware',
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
    'shoutit.middleware.UserPermissionsMiddleware',
    'shoutit.middleware.FBMiddleware',
    'shoutit.middleware.BadRequestsMiddleware',
    'shoutit.api.exceptions.APIExceptionMiddleware',
    # 'common.middleware.ProfilerMiddleware.ProfileMiddleware',
    # 'common.middleware.SqlLogMiddleware.SQLLogToConsoleMiddleware',
)

"""
=================================
            Database
=================================
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME', 'shoutit_' + SHOUTIT_ENV),
    # eg. SHOUTIT_ENV is prod, db should be shoutit_prod
        'USER': os.environ.get('DB_USER', 'shoutit'),
        'PASSWORD': os.environ.get('DB_PASSWORD', '#a\_Y9>uw<.5;_=/kUwK'),
        'HOST': os.environ.get('DB_HOST', 'db.shoutit.com'),
        'PORT': os.environ.get('DB_PORT', '5432'),
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
USE_L10N = True
USE_TZ = True
LANGUAGES = (
    ('en', _('English')),
)
DEFAULT_LANGUAGE_CODE = 'en'

"""
=================================
         Static files
=================================
"""
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
    STATIC_ROOT = os.path.join('/var', 'static')
    if not os.path.exists(STATIC_ROOT):
        os.makedirs(STATIC_ROOT)

STATICFILES_DIRS = (
    os.path.join(SRC_DIR, 'static'),
)

# Templates
TEMPLATE_DEBUG = DEBUG
TEMPLATE_DIRS = (
    os.path.join(SRC_DIR, 'templates'),
    os.path.join(SRC_DIR, 'templates', 'api_site'),
    os.path.join(SRC_DIR, 'templates', 'text_messages'),
    os.path.join(SRC_DIR, 'templates', 'html_messages'),
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
APNS_SANDBOX = os.environ.get('APNS_SANDBOX', False)
FORCE_PUSH = os.environ.get('FORCE_PUSH', False)
APNS_CERT_NAME = 'push-%s.pem' % ('prod' if PROD else 'dev')
PUSH_NOTIFICATIONS_SETTINGS = {
    'GCM_API_KEY': "AIzaSyBld5731YUMSNuLBO5Gu2L4Tsj-CrQZGIg",
    'APNS_CERTIFICATE': os.path.join(SRC_DIR, 'assets', 'certificates', 'ios', APNS_CERT_NAME),
    'APNS_HOST': "gateway.%spush.apple.com" % ('sandbox.' if APNS_SANDBOX else ''),
    'APNS_FEEDBACK_HOST': "feedback.%spush.apple.com" % ('sandbox.' if APNS_SANDBOX else '')
}
MAX_BROADCAST_RECIPIENTS = 1000

# Mixpanel
MIXPANEL_TOKEN = os.environ.get('MIXPANEL_TOKEN', 'a5774a99b9068ae66129859421ade687')
FORCE_MP_TRACKING = os.environ.get('FORCE_MP_TRACKING', False)

# Nexmo
NEXMO_API_KEY = "7c650639"
NEXMO_API_SECRET = "4ee98397"

# IP2Location
IP2LOCATION_DB_BIN = os.path.join('/opt', 'ip2location', 'IP2LOCATION-LITE-DB9.BIN')

# AntiCaptcha
ANTI_KEY = 'eb8e82bf16467103e8e0f49f6ea2924a'

"""
=================================
          Linked Apps
=================================
"""
# Facebook App
FACEBOOK_APP_ID = '353625811317277' if PROD else '1151546964858487'
FACEBOOK_APP_SECRET = '75b9dadd2f876a405c5b4a9d4fc4811d' if PROD else '8fb7b12351091e8c59c723fc3105d05a'

# Google App
GOOGLE_API = {
    'CLIENTS': {
        'web': {'FILE': os.path.join(SRC_DIR, 'assets', 'googleapiclients', 'web.json')},
        'android': {'FILE': os.path.join(SRC_DIR, 'assets', 'googleapiclients', 'android.json')},
        'ios': {'FILE': os.path.join(SRC_DIR, 'assets', 'googleapiclients', 'ios.json')},
    }
}

"""
=================================
            Mail
=================================
"""
LOG_DIR = os.path.join('/var', 'log', 'shoutit-api-' + SHOUTIT_ENV)
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

MAILCHIMP_API_KEY = 'd87a573a48bc62ff3326d55f6a92b2cc-us5'
MAILCHIMP_MASTER_LIST_ID = 'f339e70dd9'

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
POSTMARK_SMTP = {
    'default_from_email': 'Shoutit <noreply@shoutit.com>',
    'host': 'smtp.postmarkapp.com',
    'port': 587,
    'username': str('0172be86-91ee-45cd-b651-e3c761d99726'),  # str() to avoid issue in Python HMAC: http://stackoverflow.com/a/20862445/552621
    'password': str('0172be86-91ee-45cd-b651-e3c761d99726'),
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
    'postmark': POSTMARK_SMTP,
    'file': FILE_SMTP
}
EMAIL_ENV = os.environ.get('EMAIL_ENV', 'file')
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

# OAuth2 settings
OAUTH_SINGLE_ACCESS_TOKEN = True
OAUTH_ENFORCE_SECURE = ENFORCE_SECURE
OAUTH_ENFORCE_CLIENT_SECURE = True
OAUTH_DELETE_EXPIRED = True

SWAGGER_SETTINGS = {
    'api_version': '3',
    'api_path': '/',
    'protocol': 'https' if PROD else 'http',
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
        # 'contact': 'mo.chawich@gmail.com',
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
    'dsn': os.environ.get('RAVEN_DSN'),
    'string_max_length': 1000
}
FORCE_SENTRY = False
SENTRY_CLIENT = 'shoutit.api.exceptions.ShoutitRavenClient'
LOG_SQL = False

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
        'on_server_or_forced': {
            '()': 'common.log.OnServerOrForced',
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
            'filters': ['on_server_or_forced'],
        },
        'sentry_all': {
            'level': 'DEBUG',
            'class': 'raven.contrib.django.handlers.SentryHandler',
            'filters': ['on_server_or_forced'],
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

info("==================================================")
info("================= Shoutit Server =================")
info("==================================================")
info("SHOUTIT_ENV:", SHOUTIT_ENV)
info("GUNICORN:", GUNICORN)
info("BIND: {}:{}".format(ADDRESS, PORT))
info("DEBUG:", DEBUG)
info("==================================================")
info("API_LINK:", API_LINK)
info("SITE_LINK:", SITE_LINK)
info("==================================================")
info("DB_HOST, DB_PORT:", DATABASES['default']['HOST'], DATABASES['default']['PORT'])
info("REDIS_HOST, REDIS_PORT:", REDIS_HOST, REDIS_PORT)
info("ES_HOST, ES_PORT:", ES_HOST, ES_PORT)
info("==================================================")
info('FORCE_S3:', FORCE_S3)
info('STATIC_URL:', STATIC_URL)
info("==================================================")
info("EMAIL_ENV:", EMAIL_ENV)
info('FORCE_PUSH:', FORCE_PUSH)
info('APNS_SANDBOX:', APNS_SANDBOX)
info('PUSHER_ENV:', PUSHER_ENV)
info('TWILIO_ENV:', TWILIO_ENV)
info("==================================================")
