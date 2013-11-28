from datetime import timedelta
import sys,os



sys.path.append('D:/Shout/Code')
sys.path.append('/home/django/')
sys.path.append('/Users/SYRON/Desktop/Syrex/The Social Market/shout/Code/')
os.environ['DJANGO_SETTINGS_MODULE'] ='Shout.settings'

from django.core.management import setup_environ
from apps.shoutit import settings
setup_environ(settings)

from django.contrib.auth.models import User
import datetime
from django.db.models.query_utils import Q

today = datetime.datetime.today()

days = datetime.timedelta(days = int(settings.MAX_EXPIRY_DAYS))
begin = today - days


users_count = User.objects.filter(Q(Shouts__ExpiryDate__isnull = True, Shouts__DatePublished__lt = begin) | Q(Shouts__ExpiryDate__isnull = False, Shouts__ExpiryDate__lte = today)).filter( email = '').count()

choice = raw_input('enter amount of useless users you want to delete (type "all" to delete all useless users):')

if choice.lower() == 'all' :
	count = users_count
else:
	try:
		count = int(choice)
	except ValueError, e:
		sys.exit(1)
if count <= 0:
	sys.exit(1)
	
users = User.objects.filter(Q(Shouts__ExpiryDate__isnull = True, Shouts__DatePublished__lt = begin) | Q(Shouts__ExpiryDate__isnull = False, Shouts__ExpiryDate__lte = today)).filter( email = '').order_by('date_joined').distinct()[0:count]
i = 0

choice = raw_input('WARNING: deleting %d users permanently, are you sure? (yes or no):' % count)
if choice.lower() == 'yes':
	for user in users:
		if i >= count:
			break
		print ('\t deleting user %s\n' % ('(id: ' + unicode(user.id) + ', username: ' + unicode(user) + ')'))
		user.delete()
		i += 1
print('%d users have been deleted!' % i)