from settings import info, ES_URL
from elasticsearch_dsl.connections import connections

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
# Define a default global Elasticsearch client
ES = connections.create_connection(hosts=[ES_URL])


default_app_config = 'shoutit.appconfig.ShoutitConfig'

info("==================================================")
