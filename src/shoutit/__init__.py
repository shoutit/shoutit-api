from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch_dsl.connections import connections
from requests_aws4auth import AWS4Auth

from django.conf import settings

"""
=================================
          Monkey Patches
=================================
"""
# some monkey patching for global imports
import monkey_patches  # NOQA

settings.info('Monkeys: Loaded')

"""
=================================
          Elasticsearch
=================================
"""
# Define a default global Elasticsearch client
if 'es.amazonaws.com' in settings.ES_URL:
    # Connect using IAM  based authentication on AWS
    awsauth = AWS4Auth(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, 'eu-west-1', 'es')
    ES = Elasticsearch(
        hosts=[settings.ES_URL],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    connections.add_connection(alias='default', conn=ES)
else:
    ES = connections.create_connection(hosts=[settings.ES_URL])

default_app_config = 'shoutit.appconfig.ShoutitConfig'

settings.info("==================================================")
