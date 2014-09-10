__author__ = 'SYRON'

import oauth2 as oauth
import requests
import pprint

request_token_url = 'http://shoutit.syrex:8000/oauth/request_token/'
access_token_url = 'http://shoutit.syrex:8000/oauth/gplus_access_token/'
consumer = oauth.Consumer(key='123', secret='123456')
google_one_time_code = '4/-8ajNwu6D4JzxUzLwrv8CTI2HccF.wlEqZSfSb9oaPvB8fYmgkJyfLlO-kAI'
params = {'code': google_one_time_code}

# initiate request with consumer key,secret to request_token_url
oauth_request = oauth.Request.from_consumer_and_token(consumer, http_url=request_token_url)
oauth_request.sign_request(oauth.SignatureMethod_HMAC_SHA1(), consumer, None)
request_token = requests.get(request_token_url, headers=oauth_request.to_header()).json()
pprint.pprint(request_token)


# use the returned request_token in addition to user credentials to initiate another request to access_token_url
token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
oauth_request2 = oauth.Request.from_consumer_and_token(consumer, http_url=access_token_url)
oauth_request2.sign_request(oauth.SignatureMethod_HMAC_SHA1(), consumer, token)
access_token = requests.post(access_token_url, headers=oauth_request2.to_header(), params=params).json()
pprint.pprint(access_token)
