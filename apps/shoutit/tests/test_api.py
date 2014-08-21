from django.test import TestCase
from django.test.client import Client
from django.db import connection
from apps.shoutit.models import PredefinedCity
import json
import string

def patchDatabase():
    with open("deploy_scripts/deploy.sql", "r") as myfile:
        data = myfile.read()
        cursor = connection.cursor()
        cursor.execute(data)
    myfile.close()


def createCities():
    dubai = PredefinedCity(City='Dubai', EncodedCity='dubai', Country='AE', Approved=True, Latitude=25.2644,
                           Longitude=55.3117)
    dubai.save()


class APITestCase(TestCase):
    def setUp(self):
        patchDatabase()
        createCities()
        self.testClient = Client()
        response = self.testClient.post('/api/signup/', {
            'firstname': 'philip',
            'lastname': 'dizzl',
            'email': 'philip@bitstars.com',
            'password': 'yolo',
            'confirm_password': 'yolo'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')

    def test_api(self):
        self.shout_stream()
        self.nearby_shouts()
        self.shout_clusters()

    def shout_stream(self):
        response = self.testClient.get('/api/shouts/stream/')
        print type(response)
        print response.content
        print type(response.content)
        print string.find(response.content, "[")
        parsed = json.loads(response.content)
        print type(parsed)
        print(parsed[0])
        parsed2 = json.loads(parsed[0])
        print json.dumps(parsed2, sort_keys=True, indent=4)
        self.assertEqual(response.status_code, 200)

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