from django.test import TestCase
from django.test.client import Client
from django.db import connection
from apps.shoutit.models import PredefinedCity


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
        self.client = Client()
        response = self.client.post('/api/signup/', {
            'firstname': 'philip',
            'lastname': 'dizzl',
            'email': 'philip@bitstars.com',
            'password': 'yolo',
            'confirm_password': 'yolo'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')

    def test_get_shouts(self):
        response = self.client.get('/api/shouts/stream/')
        print(response)
        self.assertEqual(response.status_code, 200)