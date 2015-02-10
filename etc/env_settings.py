import os

VIRTUAL_ENV = os.environ.get('VIRTUAL_ENV')

if VIRTUAL_ENV:
    print "VIRTUAL_ENV", VIRTUAL_ENV
    BACKEND_DIR = os.environ.get('BACKEND_DIR')
    DJANGO_DIR = BASE_DIR = os.environ.get('DJANGO_DIR')
    ENV_DIR = os.environ.get('ENV_DIR')
    ENV = os.environ.get('ENV')
    LOG_DIR = os.environ.get('LOG_DIR')

else:
    print "LOCAL"
    BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    DJANGO_DIR = os.path.join(BACKEND_DIR, 'src')
    ENV_DIR = os.path.dirname(BACKEND_DIR)
    ENV = os.path.basename(ENV_DIR)
    LOG_DIR = os.path.join('var', 'log', 'opt', ENV)

if not (BACKEND_DIR and DJANGO_DIR and ENV_DIR and ENV and LOG_DIR):
    raise EnvironmentError("BACKEND_DIR, DJANGO_DIR, ENV_DIR, ENV and LOG_DIR can not be None. "
                           "Deactivate the virtualenv if you are running manage.py directly or run start.sh")


# Local or Dev or Prod
LOCAL = ENV == 'shoutit_backend_local'
ON_SERVER = not LOCAL
DEV = ON_SERVER and ENV == 'shoutit_backend_dev'
PROD = ON_SERVER and ENV == 'shoutit_backend_prod'
