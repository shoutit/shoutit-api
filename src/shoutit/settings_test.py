from shoutit.settings import *

REST_FRAMEWORK['TEST_REQUEST_DEFAULT_FORMAT'] = 'json'

DDF_FIELD_FIXTURES = {
    'django.contrib.postgres.fields.hstore.HStoreField': lambda: {},
}
DDF_FILL_NULLABLE_FIELDS = False
