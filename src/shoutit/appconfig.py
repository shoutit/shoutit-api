from django.apps import AppConfig


class ShoutitConfig(AppConfig):
    name = 'shoutit'
    label = 'shoutit'
    verbose_name = "Shoutit API"

    def ready(self):
        from elasticsearch import Elasticsearch, RequestsHttpConnection, RequestError, ConnectionTimeout
        from elasticsearch_dsl.connections import connections
        from requests_aws4auth import AWS4Auth
        from django.conf import settings
        from shoutit.models import LocationIndex, ShoutIndex
        from shoutit.utils import error_logger

        import shoutit
        # Todo (Nour): Cleanup!
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

        shoutit.ES = ES

        # Initiate the index if not initiated
        try:
            LocationIndex.init()
        except RequestError:
            pass
        except ConnectionTimeout:
            error_logger.warn("ES Server is down", exc_info=True)

        # Initiate the index if not initiated
        try:
            ShoutIndex.init()
        except RequestError:
            pass
        except ConnectionTimeout:
            error_logger.warn("ES Server is down", exc_info=True)
