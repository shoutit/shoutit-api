from sss3_zones import *
import sys,os
import MySQLdb
import MySQLdb.cursors
from twilio.rest import TwilioRestClient
account = "AC68c05fc538824b5e9939ef7e2129a2a6"
token = "abdbd895fbf816e2d898be7e1b27a6dd"
client = TwilioRestClient(account, token)


def FormatList(list):
	return ','.join(['%s'] * len(list))



countries = ['']
now = datetime.today() + timedelta(hours=4)
print now
for zone in ZONES:
	if not zone.has_key('sms_from'):
		continue
	if zone['sms_from'] <= now <= zone['sms_to']:
		print zone['name'], ' Added to SMSing List'
		countries += zone['countries']
if countries == ['']:
	print 'No Zones to be SMSed at this time'
	sys.exit(0)


many = 200
errors = 0
#80.227.53.34
db = MySQLdb.connect(host="80.227.53.34", user="noor", passwd='sni4hot*', db="sss",charset = "utf8", use_unicode = True, cursorclass=MySQLdb.cursors.DictCursor)
cur = db.cursor()
cur.execute("SELECT id,mobile FROM ads WHERE fetched=2 and country in(%s) ORDER BY rand() limit %s"%(FormatList(countries),str(many)),countries)
mobiles = cur.fetchall()
if len(mobiles) == 0:
	print "No Mobiles to Blast"
	sys.exit(0)
cur.execute("UPDATE ads SET fetched=4 WHERE fetched=2 and mobile IN(%s)" % str(','.join([m['mobile'] for m in mobiles])))
print 'updating db done'

print 'Going to send %d SMS\'s' % (len(mobiles))

for m in mobiles:

	try:
		ad_id = m['id']
		mobile = m['mobile']
		text = ['Log on to Shoutit.com to join the future of marketplaces. A location-based market that allows you \'shout\' your needs directly to your local community.'
				,'Log on to Shoutit.com and join the future of buying and selling. Shout what you want to your local community and build your shopping profile.']

		text = text[1]
		if ad_id.find('gum') != -1:
			message = client.sms.messages.create(to="+"+mobile, from_="+442033224455",body=text)
			print 'sms via Twilio UK to mobile: %s sent' % mobile

		elif ad_id.find('kij') != -1:
			message = client.sms.messages.create(to="+"+mobile, from_="+16479315866",body=text)
			print 'sms via Twilio CA to mobile: %s sent' %  mobile

	except Exception, e:
		errors += 1
		cur.execute("UPDATE ads SET fetched=2, note='Error Blasting' WHERE fetched=4 and mobile ='%s'" % mobile)
		print 'sms to mobile: %s error: %s' % ( mobile, e.message)


print 'Done sms-ing %d users' % (len(mobiles)-errors)
