from sss3_zones import *
import MySQLdb
import MySQLdb.cursors
import sys
import urllib2,urllib
import time

def FormatList(list):
	return ','.join(['%s'] * len(list))


countries = {
	1:{
		'names':[],
	},
	2:{
		'names':[],
	}
}
now = datetime.today()# + timedelta(hours=4)
print now
for zone in ZONES:
	if zone['save_from'] <= now <= zone['save_to']:
		print zone['name'], ' Added to Saving List'
		countries[zone['since']]['names'] += zone['countries']
if countries[1]['names'] == [] and countries[2]['names'] == []:
	print 'No Zones to be saved at this time'
	sys.exit(0)

shouts = []

many = 100
errors = 0

#db = MySQLdb.connect(host="192.168.1.2", user="noor", passwd='sni4hot*', db="sss",charset = "utf8", use_unicode = True, cursorclass=MySQLdb.cursors.DictCursor)
db = MySQLdb.connect(host="80.227.53.34", user="noor", passwd='sni4hot*', db="sss",charset = "utf8", use_unicode = True, cursorclass=MySQLdb.cursors.DictCursor)
cur = db.cursor()

for group in countries:
	if countries[group]['names'] == []:
		continue
#	group_date = (now - timedelta(days=group)).strftime('%Y-%m-%d 00:00:00')
#	cur.execute("SELECT id,json FROM ads WHERE fetched=1 and country in(%s) and date='%s' ORDER BY RAND() limit %s"%(FormatList(countries[group]['names']),group_date,str(many)),countries[group]['names'])
	cur.execute("SELECT id,json FROM ads WHERE fetched=1 and country in(%s) ORDER BY RAND() limit %s"%(FormatList(countries[group]['names']),str(many)),countries[group]['names'])
	shouts += cur.fetchall()


if len(shouts) == 0:
	print "No Ads to Save"
	sys.exit(0)

ids = ['"%s"'%shout['id'] for shout in shouts]
print 'Going to save %d ads\'s' % (len(ids))
up = "UPDATE ads SET fetched=-3 WHERE id IN(%s)" % str(','.join(ids))
cur.execute(up)
print 'Saving started!'

for shout in shouts:
	print str(list(shouts).index(shout) + 1)+ ' : ',

	if shout['json']:

		try :
			# POST to /api/sss/
			data = urllib.urlencode({'json':shout['json'].encode('utf-8')})
			response = urllib2.urlopen('http://localhost:8000/api/sss/', data, timeout=200)

			# Success after receiving api response
			if response.code == 200:
				cur.execute("UPDATE ads SET fetched=3, fetch_date=NOW(), note=%s WHERE id=%s", ('Shouted!', shout['id']))
				print 'Shout id: %s Saved!' % (shout['id'])
			else:
				cur.execute("UPDATE ads SET fetched=-4, fetch_date=NOW(), note=%s WHERE id=%s", (response.read(), shout['id']))
				print 'Shout id: %s Saving Error!' % shout['id']
				errors += 1
				continue

		except BaseException,e:
			cur.execute("UPDATE ads SET fetched=-4, fetch_date=NOW(), note=%s WHERE id=%s", ('Sending Error', shout['id']))
			print 'Shout id: %s Sending Error! | %s' % (shout['id'], e)
			errors += 1
			continue
	else:
		print 'JSON Error: No Json'
		cur.execute("UPDATE ads SET fetched=-4, fetch_date=NOW(), note=%s WHERE id=%s", ('JSON Error', shout['id']))
		errors += 1
		continue
	time.sleep(1)

print 'Done Saving %d Shouts' % (len(shouts)-errors)