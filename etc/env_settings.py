import os

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
DJANGO_DIR = os.path.join(BACKEND_DIR, 'src')
ENV_DIR = os.path.dirname(BACKEND_DIR)
ENV = os.path.basename(ENV_DIR)
LOG_DIR = os.path.join(ENV_DIR, 'log')

# Local or Dev or Prod
LOCAL = ENV == 'shoutit_backend_local'
ON_SERVER = not LOCAL
DEV = ON_SERVER and ENV == 'shoutit_backend_dev'
PROD = ON_SERVER and ENV == 'shoutit_backend_prod'
