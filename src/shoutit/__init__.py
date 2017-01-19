from settings_env import info

"""
=================================
          Monkey Patches
=================================
"""
# some monkey patching for global imports
import monkey_patches  # NOQA

info('Monkeys: Loaded')

"""
=================================
          Elasticsearch
=================================
"""
# Placeholder for ES instance which will be defined once the app is ready in appconfig
ES = None

default_app_config = 'shoutit.appconfig.ShoutitConfig'

info("==================================================")
