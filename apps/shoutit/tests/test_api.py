from django.test import TestCase
from django.test.client import Client


class APITestCase(TestCase):
    def test_index_page(self):
        c = Client()
        response = c.get('', follow=True)
        # print(response)

    def test_api_stuff(self):
        c = Client()
        response = c.get('/xhr/live_events/', {'url_encoded_city': 'dubai', 'timestamp': '', '_': '1408356493749'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')