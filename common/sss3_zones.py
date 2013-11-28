from datetime import datetime,timedelta

ZONES = [
#		{
#		'name':'USA1 - 2',
#		'countries': ['newyork', 'miami', 'atlanta', 'boston', 'detroit', 'philadelphia', 'washingtondc','baltimore','charlotte','columbusoh', 'pittsburgh', 'raleigh', 'tampabay', 'orlando', 'newark'],
#		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
#		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=8, minute=0, second=0),
#		'since':2,
#		'many':10,
#		},
#		{
#		'name':'CA1 - 2',
#		'countries': ['kitchener','toronto'],
#		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
#		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=8, minute=0, second=0),
#		'since':2,
#		'many':50,
#		},
#		{
#		'name':'USA2 - 2',
#		'countries': ['chicago', 'houston','cincinnati','dallas','denver', 'indianapolis', 'milwaukee', 'stlouis'],
#		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
#		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=9, minute=0, second=0),
#		'since':2,
#		'many':10,
#		},
#		{
#		'name':'CA2 - 2',
#		'countries': ['xxxx'],
#		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
#		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=9, minute=0, second=0),
#		'since':2,
#		'many':50,
#		},
#		{
#		'name':'USA3 - 2',
#		'countries': ['losangeles', 'bayarea', 'lasvegas', 'phoenix', 'seattle','centralvalley','inlandempire', 'orangecounty', 'portlandor', 'sacramento', 'sandiego'],
#		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
#		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=10, minute=0, second=0),
#		'since':2,
#		'many':10,
#		},
#		{
#		'name':'CA3 - 2',
#		'countries': ['xxxx'],
#		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
#		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=10, minute=0, second=0),
#		'since':2,
#		'many':50,
#		},
#		{
#		'name':'UK - 2',
#		'countries': ['london', 'birmingham', 'glasgow','sheffield', 'edinburgh','liverpool','manchester', 'bristol', 'cardiff', 'coventry', 'sunderland', 'leicester','nottingham', 'brighton' ,'oxford' ,'leeds'],
#		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
#		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=4, minute=0, second=0),
#		'since':2,
#		'many':50,
#		},
		{
		'name':'India',
		'countries': ['mumbai', 'newdelhi', 'bangalore', 'chennai', 'hyderabad', 'pune', 'chandigarhcity', 'kolkata', 'thane', 'gurgaon', 'kerala'],
		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=21, minute=59, second=0),
		'sms_from':(datetime.today()+ timedelta(hours=4)).replace(hour=10, minute=0, second=0),
		'sms_to':(datetime.today()+ timedelta(hours=4)).replace(hour=11, minute=59, second=0),
		'since':1,
		'many':7,
		},
		{
		'name':'UAE',
		'countries': ['uae'],
		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'sms_from':(datetime.today()+ timedelta(hours=4)).replace(hour=10, minute=0, second=0),
		'sms_to':(datetime.today()+ timedelta(hours=4)).replace(hour=11, minute=59, second=0),
		'since':1,
		'many':7,
		},
		{
		'name':'MENA',
		'countries': ['egypt','ksa','jordan','qatar','lebanon'],
		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'sms_from':(datetime.today()+ timedelta(hours=4)).replace(hour=11, minute=0, second=0),
		'sms_to':(datetime.today()+ timedelta(hours=4)).replace(hour=11, minute=59, second=0),
		'since':1,
		'many':2,
		},
		{
		'name':'UK - 1',
		'countries': ['london', 'birmingham', 'glasgow','sheffield', 'edinburgh','liverpool','manchester', 'bristol', 'cardiff', 'coventry', 'sunderland', 'leicester','nottingham', 'brighton' ,'oxford' ,'leeds'],
		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'sms_from':(datetime.today()+ timedelta(hours=4)).replace(hour=15, minute=0, second=0),
		'sms_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'since':1,
		'many':50,
		},
		{
		'name':'USA1 - 1',
		'countries': ['newyork', 'miami', 'atlanta', 'boston', 'detroit', 'philadelphia', 'washingtondc','baltimore','charlotte','columbusoh', 'pittsburgh', 'raleigh', 'tampabay', 'orlando', 'newark'],
		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'sms_from':(datetime.today()+ timedelta(hours=4)).replace(hour=19, minute=0, second=0),
		'sms_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'since':1,
		'many':10,
		},
		{
		'name':'CA1 - 1',
		'countries': ['kitchener','toronto'],
		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'sms_from':(datetime.today()+ timedelta(hours=4)).replace(hour=19, minute=0, second=0),
		'sms_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'since':1,
		'many':50,
		},
		{
		'name':'USA2 - 1',
		'countries': ['chicago', 'houston','cincinnati','dallas','denver', 'indianapolis', 'milwaukee', 'stlouis'],
		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'sms_from':(datetime.today()+ timedelta(hours=4)).replace(hour=20, minute=0, second=0),
		'sms_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'since':1,
		'many':10,
		},
		{
		'name':'CA2 - 1',
		'countries': ['xxx'],
		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'sms_from':(datetime.today()+ timedelta(hours=4)).replace(hour=20, minute=0, second=0),
		'sms_to':(datetime.today()+ timedelta(hours=4)).replace(hour=20, minute=59, second=0),
		'since':1,
		'many':50,
		},
		{
		'name':'USA3 - 1',
		'countries': ['losangeles', 'bayarea', 'lasvegas', 'phoenix', 'seattle','centralvalley','inlandempire', 'orangecounty', 'portlandor', 'sacramento', 'sandiego'],
		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'sms_from':(datetime.today()+ timedelta(hours=4)).replace(hour=21, minute=0, second=0),
		'sms_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'since':1,
		'many':10,
		},
		{
		'name':'CA3 - 1',
		'countries': ['montreal','vancouver','calgary','ottawa','edmonton','winnipeg','hamilton'],
		'save_from':(datetime.today()+ timedelta(hours=4)).replace(hour=0, minute=0, second=0),
		'save_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'sms_from':(datetime.today()+ timedelta(hours=4)).replace(hour=21, minute=0, second=0),
		'sms_to':(datetime.today()+ timedelta(hours=4)).replace(hour=23, minute=59, second=0),
		'since':1,
		'many':50,
		},
]