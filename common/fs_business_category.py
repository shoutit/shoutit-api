import sys,os

sys.path.append('D:/Shout/Code')
os.environ['DJANGO_SETTINGS_MODULE'] ='Shout.settings'

from django.core.management import setup_environ
import apps.shoutit.settings as settings
setup_environ(settings)

from apps.shoutit.constants import BUSINESS_SOURCE_TYPE_FOURSQUARE
from apps.shoutit.models import BusinessCategory
import urllib2, json

def traverse_categories(categories, parent, f):
	for category in categories:
		cat = f(category, parent)
		if category.has_key('categories') and len(category['categories']) > 0:
			traverse_categories(category['categories'], cat, f)

json_string = urllib2.urlopen('https://api.foursquare.com/v2/venues/categories?client_id=OHK5WCHEXIFGFLQ2MG4CWNCA3BIF4QS3QOLXT4H0TMASHDZQ&client_secret=R1COJBNHS0HDSADBX0D1QSGBHWYFZBXVA0WE0THNY2ZSZEEM&v=20120702').read()
categories = json.loads(json_string)['response']['categories']
def f(category, parent):
	c = BusinessCategory(Name = category['name'], Source = BUSINESS_SOURCE_TYPE_FOURSQUARE, SourceID = category['id'], Parent = parent)
	c.save()
	return c
traverse_categories(categories, None, f)
