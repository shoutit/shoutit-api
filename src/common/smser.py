import sys
import urllib
import urllib2

import os

import settings
from sss3_zones import *
import MySQLdb
import MySQLdb.cursors
from twilio.rest import TwilioRestClient


account = "AC68c05fc538824b5e9939ef7e2129a2a6"
token = "abdbd895fbf816e2d898be7e1b27a6dd"
client = TwilioRestClient(account, token)

from django.utils.translation import ugettext as _

sys.path.append('/home/django/')
# sys.path.append('/Users/SYRON/Desktop/Syrex/The Social Market/shout/Code/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'Shout.settings'

from django.core.management import setup_environ

setup_environ(settings)
from shoutit.models import Profile, Trade
from shoutit import utils


def FormatList(list):
    return ','.join(['%s'] * len(list))


countries = ['']
now = datetime.today()
print now
for zone in ZONES:
    if 'sms_from' not in zone:
        continue
    if zone['sms_from'] <= now <= zone['sms_to']:
        print zone['name'], ' Added to SMSing List'
        countries += zone['countries']
if countries == ['']:
    print 'No Zones to be SMSed at this time'
    sys.exit(0)

many = 200
errors = 0
db = MySQLdb.connect(host="80.227.53.34", user="noor", passwd='sni4hot*', db="sss", charset="utf8", use_unicode=True,
                     cursorclass=MySQLdb.cursors.DictCursor)
cur = db.cursor()

#sms_date = (now - timedelta(days=2)).strftime('%Y-%m-%d 00:00:00')
#cur.execute("SELECT mobile FROM ads WHERE fetched=3 and country in(%s) and date='%s' ORDER BY rand() limit %s"%(FormatList(countries),sms_date,str(many)),countries)
#cur.execute("SELECT mobile FROM ads WHERE fetched=3 and country in(%s) ORDER BY rand() limit %s"%(FormatList(countries),str(many)),countries)
cur.execute("SELECT mobile FROM ads WHERE fetched=3 ORDER BY rand() limit %s", many)
ads = cur.fetchall()
mobiles = [ad['mobile'] for ad in ads]
print 'Found %d mobiles\'s' % (len(mobiles))
if len(mobiles) == 0:
    print "No More Mobiles to SMS"
    sys.exit(0)

cur.execute("UPDATE ads SET fetched=4 WHERE fetched=3 and mobile IN(%s)" % str(','.join(mobiles)))
print 'updating db done'

print 'checking users'
users = Profile.objects.filter(isSSS=True, Mobile__in=mobiles, user__is_active=False, isSMS=False)
print 'Going to send %d SMS\'s' % (len(users))

for user in users:
    print str(list(users).index(user) + 1) + ' : ',
    try:
        shout = Trade.objects.get_valid_trades().filter(OwnerUser=user.user).select_related('Item')
        content = 'an advertisement'
        if len(shout):
            content = utils.remove_non_ascii(shout[0].Item.Name)

        link = 'shoutit.com/' + user.LastToken.Token
        title = utils.get_shout_name_preview(content, 22)

        text = _(
            'There is potential interest in your ad \'%(shout_title)s\' on Shoutit.\nVisit Region\'s first FREE social marketplace %(link)s to get started') % {
               'shout_title': title, 'link': link}

        quoted_text = urllib.quote(text)
        mobile = user.Mobile

        if user.Country == 'US':
            message = client.sms.messages.create(to="+" + mobile, from_="+16464309339", body=text)
            print 'sms via Twilio US to: %s mobile: %s sent' % (user.user.pk, mobile)
            user.isSMS = True
            user.save()

        elif user.Country == 'GB':
            message = client.sms.messages.create(to="+" + mobile, from_="+442033224455", body=text)
            print 'sms via Twilio UK to: %s mobile: %s sent' % (user.user.pk, mobile)
            user.isSMS = True
            user.save()

        elif user.Country == 'CA':
            message = client.sms.messages.create(to="+" + mobile, from_="+16479315866", body=text)
            print 'sms via Twilio CA to: %s mobile: %s sent' % (user.user.pk, mobile)
            user.isSMS = True
            user.save()

        else:
            sms_url = 'https://www.smsglobal.com/http-api.php?&action=sendsms&user=syrexme&password=25600696&from=Shoutit.com&to=%s&text=%s' % (
            mobile, quoted_text)

            sms_res = urllib2.urlopen(sms_url, timeout=10).read()
            if sms_res.find('OK: 0') != -1:
                print 'sms to: %s mobile: %s sent' % (user.user.pk, mobile)
                user.isSMS = True
                user.save()
            else:
                print 'sms via Smsglobal to: %s mobile: %s error: %s' % (user.user.pk, mobile, sms_res)
                cur.execute("UPDATE ads SET fetched=3 WHERE fetched=4 and mobile ='%s'" % mobile)
                errors += 1


    except Exception, e:
        errors += 1
        cur.execute("UPDATE ads SET fetched=3 WHERE fetched=4 and mobile ='%s'" % user.Mobile)
        print 'sms to: %s mobile: %s error: %s' % (user.user.pk, user.Mobile, e.message)

#	time.sleep(1)

print 'Done sms-ing %d users' % (len(users) - errors)