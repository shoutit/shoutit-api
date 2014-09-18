
LOCAL_DEV = True
DIRNAME = os.path.dirname(os.path.abspath(__file__))
if LOCAL_DEV:
    INTERNAL_IPS = ('127.0.0.1',)

_parent = lambda x: os.path.normpath(os.path.join(x, '..'))
SATCHMO_DIRNAME = _parent(_parent(DIRNAME))







MEDIA_ROOT = os.path.join(os.path.dirname(__file__), 'ShoutWebsite')
MEDIA_URL = ''
STATIC_ROOT = ''
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'

TEMP_UPLOAD_PATH = os.path.join(MEDIA_ROOT, 'static', 'temp')
TEMP_UPLOAD_URL = '/static/temp/'

PROFILE_LOG_BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'profiling')
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#	'compressor.finders.CompressorFinder',
)
SECRET_KEY = '8xya^3^n_8d@c^lips0@!!3swh#7xyygf3w@)lsobv+!ni)x94'





INSTALLED_APPS = (
	'django.contrib.sites',
    'django.contrib.messages',

#	'satchmo_store.shop',
	
	'django.contrib.admin',
	'grappelli',
	'django.contrib.auth',
	'django.contrib.admindocs',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
	'django.contrib.sitemaps',
    'django.contrib.staticfiles',
	'widget_tweaks',
    'ActivityLogger',
    'ShoutWebsite',
	
#	'keyedcache',
#	'livesettings',
#	'l10n',
#	'sorl.thumbnail',
#	'product',
#	'product.modules.subscription',
#    'payment',
#	'satchmo_utils',
#	'app_plugins',
#	'subscription',
	
#	'south',
	'piston',
	'django_mobile',
	"djcelery",
	'paypal.standard.ipn',
	'paypal.standard.pdt',
)

PAYPAL_IDENTITY_TOKEN = 't9KJDunfc1X12lnPenlifnxutxvYiUOeA1PfPy6g-xpqHs5WCXA7V7kgqXO' #'SeS-TUDO3rKFsAIXxQOs6bjn1_RVrqBJE8RaQ7hmozmkXBuNnFlFAhf7jJO'
PAYPAL_RECEIVER_EMAIL = 'nour@syrex.me'
PAYPAL_PRIVATE_CERT = os.path.join(os.path.dirname(__file__), 'ShoutWebsite', 'static', 'Certificates', 'PayPal', 'paypal-private-key.pem')
PAYPAL_PUBLIC_CERT = os.path.join(os.path.dirname(__file__), 'ShoutWebsite', 'static', 'Certificates', 'PayPal', 'paypal-public-key.pem')
PAYPAL_CERT = os.path.join(os.path.dirname(__file__), 'ShoutWebsite', 'static', 'Certificates', 'PayPal', 'paypal-cert.pem')
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

SATCHMO_SETTINGS = {
    'SHOP_BASE' : '',
    'MULTISHOP' : True,
}

LOGFILE = "satchmo.log"
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
		'message_only' : {
			'format': '%(message)s'
		}
	},
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
		'sql_file': {
			'class' : 'logging.FileHandler',
			'level' : 'INFO',
			'filename': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'sql.log'),
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

#Mail Settings
DEFAULT_FROM_EMAIL = 'ShoutIt <info@shoutit.com>'
EMAIL_HOST = 'localhost'    #TODO: SET THIS BEFORE DEPLOYMENT
EMAIL_PORT = '25'
EMAIL_HOST_USER = 'admin'   #TODO: SET THIS BEFORE DEPLOYMENT
EMAIL_HOST_PASSWORD = 'password'    #TODO: SET THIS BEFORE DEPLOYMENT
EMAIL_USE_TLS = False
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'  #TODO: REMOVE THIS BEFORE DEPLOYMENT
EMAIL_FILE_PATH = os.path.join(os.path.dirname(__file__), 'messages')   #TODO: REMOVE THIS BEFORE DEPLOYMENT

SEND_GRID_SMTP_HOST = 'smtp.sendgrid.net'
SEND_GRID_SMTP_USERNAME = 'shoutit'
SEND_GRID_SMTP_PASSWORD = 'Syrex6me'

#Auth Settings
LOGIN_URL = '/signin/'
LOGIN_URL_MODAL = '/#signin/'
LOGOUT_URL = '/signout/'
ACTIVATE_URL = '/activate/'
ACTIVATE_URL_MODAL = '/#activate/'

#SITE_HOST
#if False:
#    SITE_HOST = 'shout.ae'
#else:# My Development
SITE_HOST = '127.0.0.1:80'

#COMPRESS_ENABLED = True
#COMPRESS_ROOT = os.path.join(os.path.dirname(__file__), 'ShoutWebsite/static')
#COMPRESS_PARSER = 'compressor.parser.BeautifulSoupParser'

try:
    import redis
    SESSION_ENGINE = 'redis_session_backend'
    CACHES = {
		'default': {
			'BACKEND' : 'redis_cache.RedisCache',
			'LOCATION' : 'shoutit.syrex:6379',
			'TIMEOUT': 12 * 60 * 60,
		}
	}
except ImportError:
    redis = ''
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
    CACHES = {
		'default': {
			'BACKEND' : 'django.core.cache.backends.locmem.LocMemCache',
			'TIMEOUT': 240,
		}
	}

ACCOUNT_ACTIVATION_DAYS = 7

SOUTH_TESTS_MIGRATE = False
REALTIME_SERVER_URL = 'http://shoutit.syrex:7772/' #'www.shoutit.com'
REALTIME_SERVER_ADDRESS = 'shoutit.syrex'
REALTIME_SERVER_TCP_PORT = 7771
REALTIME_SERVER_HTTP_PORT = 7772
REALTIME_SERVER_API_PORT = 7773
RABBIT_MQ_HOST = 'shoutit.syrex'
RABBIT_MQ_PORT = 5672
SHOUT_IT_DOMAIN = 'shoutit.syrex:8008' #'www.shoutit.com'
IS_SITE_SECURE = False #True

SESSION_REDIS_HOST = 'shoutit.syrex'
SESSION_REDIS_PORT = 6379
REDIS_SOCKET_TIMEOUT = 30

HAYSTACK_SITECONF = 'Shout.search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8983/solr'

CLOUD_FILES_AUTH = 'syrexme'
CLOUD_FILES_KEY = '1a0386c347776588f5aa08cf8dce0877'
CLOUD_FILES_SERVICE_NET = False #True

SHOUT_IMAGES_CDN = 'c296814.r14.cf1.rackcdn.com'

FACEBOOK_APP_ID = '353625811317277'
FACEBOOK_APP_SECRET = '75b9dadd2f876a405c5b4a9d4fc4811d'

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

SMS_SERVICE_WSDL_URL = 'https://www.smsglobal.com/mobileworks/soapserver.php?wsdl'
SMS_SERVICE_USERNAME = 'syrexme'
SMS_SERVICE_PASSWORD = '25600696'

PROFANITIES_LIST = ('ass', 'ass lick', 'asses', 'asshole', 'assholes', 'asskisser', 'asswipe',
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
					'whore', 'wop')