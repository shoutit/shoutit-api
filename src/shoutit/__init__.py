# some monkey patching for global imports
import monkey_patches  # NOQA
from settings import info


info('Monkeys: Loaded')
info("==================================================")
default_app_config = 'shoutit.appconfig.ShoutitConfig'
