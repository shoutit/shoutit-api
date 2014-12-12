from django.test import TestCase
from django.test.client import Client
from apps.shoutit.models import Profile
import json
import string

GET_EXTRA = {

}


class APITestCase(TestCase):
    fixtures = ['initial_data']

    def setUp(self):
        self.testClient = Client()

        # response = self.testClient.post('/api/signup/', {
        #     'firstname': 'philip',
        #     'lastname': 'dizzl',
        #     'email': 'philip@bitstars.com',
        #     'password': 'yolo',
        #     'confirm_password': 'yolo'
        # })
        # self.assertEqual(response.status_code, 201)
        # self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')

    def test_api(self):
        self.get_request_token()
        print Profile.objects.all()
        # self.shout_stream()
        #self.nearby_shouts()
        #self.shout_clusters()
        #self.get_currencies()
        #self.shout_buy()

    def get_request_token(self):
        response = self.testClient.get('/oauth/request_token/',)
        print response

    def shout_stream(self):
        response = self.testClient.get('/api/shouts/stream/')
        parsed = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(parsed['shouts'], [])
        self.assertEqual(parsed['count'], 0)
        self.assertEqual(parsed['messages'], [])

    def nearby_shouts(self):
        response = self.client.get('/api/shouts/nearby', {
            # Aachen BB "((50.75315090356295, 6.008417663574164), (50.79537870169773, 6.171753463745063))"
            'DownLeftLat': '50.75315090356295',
            'DownLeftLng': '6.008417663574164',
            'UpRightLat': '50.79537870169773',
            'UpRightLng': '6.171753463745063'
        }, follow=True)
        print(response)
        self.assertEqual(response.status_code, 200)

    def shout_clusters(self):
        response = self.client.get('/api/shouts/nearby/clusters/', {
            # Aachen BB "((50.75315090356295, 6.008417663574164), (50.79537870169773, 6.171753463745063))"
            'bottomRightLatitude': '50.75315090356295',
            'topLeftLongitude': '6.008417663574164',
            'topLeftLatitude': '50.79537870169773',
            'bottomRightLongitude': '6.171753463745063'
        }, follow=True)
        print(response)
        self.assertEqual(response.status_code, 200)

    def get_currencies(self):
        response = self.client.get('/api/currencies/')
        print response
        self.assertEqual(response.status_code, 200)

    def shout_buy(self):
        response = self.client.post('/api/shout/buy', {
            'price': '42.5',
            'currency': 'EUR',
            'name': 'Nice offer',
            'description': 'BlaBla Buy this BlaBla',
            'tags': 'superman chicken',
            'location': 'bitstars',
            'country': 'Germany',
            'city': 'Aachen'
        }, follow=True)
        print response
        self.assertEqual(response.status_code, 200)




################ oauth flow

# import urlparse
# import oauth2 as oauth
# import requests
# import pprint
#
# request_token_url = 'http://shoutit.com:8000/oauth/request_token/'
# access_token_url = 'http://shoutit.com:8000/oauth/access_token/'
# consumer = oauth.Consumer(key='123', secret='123456')
#
# # initiate request with consumer key,secret to request_token_url
# oauth_request = oauth.Request.from_consumer_and_token(consumer, http_url=request_token_url)
# oauth_request.sign_request(oauth.SignatureMethod_HMAC_SHA1(), consumer, None)
# request_token = requests.get(request_token_url, headers=oauth_request.to_header()).json()
# pprint.pprint(request_token)
#
#
# # use the returned request_token in addition to user credentials to initiate another request to access_token_url
# token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
# oauth_request2 = oauth.Request.from_consumer_and_token(consumer, http_url=access_token_url)
# oauth_request2.sign_request(oauth.SignatureMethod_HMAC_SHA1(), consumer, token)
# access_token = requests.get(access_token_url, headers=oauth_request2.to_header(), params={'credential':'syron', 'password': '123'}).json()
# pprint.pprint(access_token)
