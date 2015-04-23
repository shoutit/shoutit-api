# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import random

from django.core.management.base import BaseCommand
from django.http import HttpRequest
from rest_framework.request import Request
import time
from shoutit.api.v2.serializers import ShoutDetailSerializer
from shoutit.models import *
from shoutit.permissions import INITIAL_USER_PERMISSIONS, ACTIVATED_USER_PERMISSIONS
from shoutit.utils import generate_password


class Command(BaseCommand):
    help = 'Fill database with test shouts'
    max_users = 100
    min_shouts = 10
    max_shouts = 10000

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('num_shouts', nargs=1, type=int)

    def handle(self, *args, **options):

        users = list(User.objects.filter(username__startswith='test_100'))
        categories = list(Category.objects.all().prefetch_related('tags'))
        cities = PredefinedCity.objects.all()

        # adding test users if we don't have them
        if not len(users) == self.max_users:
            for i in range(self.max_users):
                username = 'test_' + str(1000000 + i)
                email = username + '@shoutit.com'
                user, _ = User.objects.get_or_create(username=username, first_name='user', last_name=username, email=email)
                if _:
                    user.password = generate_password()
                    user.save()
                    user.activate()
                try:
                    user.profile
                except AttributeError:
                    profile = Profile(user=user)
                    profile.image = 'https://s3-eu-west-1.amazonaws.com/shoutit-user-image-original/9ca75a6a-fc7e-48f7-9b25-ec71783c28f5-1428689093983.jpg'
                    city = random.choice(cities)
                    profile.city = city.city
                    profile.country = city.country
                    profile.latitude = city.latitude + random.uniform(-3, 3) / 100.0
                    profile.longitude = city.longitude + random.uniform(-3, 3) / 100.0
                    profile.save()
                self.stdout.write('city: {}, lat: {}, lng: {}'.format(user.profile.city, user.profile.latitude, user.profile.longitude))
                users.append(user)

        for i in range(max(options.get('num_shouts')[0], self.min_shouts)):
            # for i in range(1000):
            user = random.choice(users)
            type = random.choice(['offer', 'request'])
            category = random.choice(categories)
            city = random.choice(cities)
            tags = random.sample(category.tags.all().values_list('name', flat=1), random.randint(1, min(5, category.tags.count())))
            images = [
                "https://s3-eu-west-1.amazonaws.com/shoutit-shout-image-original/opo0928a.jpg",
                "https://s3-eu-west-1.amazonaws.com/shoutit-shout-image-original/heic1501a.jpg",
                "https://s3-eu-west-1.amazonaws.com/shoutit-shout-image-original/heic0702a.jpg"
            ]
            random.shuffle(images)
            videos = [
                {
                    "url": "https://www.youtube.com/watch?v=ib-lvhJnV0Q",
                    "thumbnail_url": "https://i.ytimg.com/vi/ib-lvhJnV0Q/hqdefault.jpg",
                    "provider": "youtube",
                    "id_on_provider": "ib-lvhJnV0Q",
                    "duration": 240
                }
            ]
            shout_data = {
                "type": type,
                "title": "{0} {1} in {2} at {3:0.0f}".format(category.name, type, city.city, time.time()),
                "text": "".format(" ".join(tags)),
                "price": random.randint(0, 1000),
                "currency": "EUR",
                "images": images,
                "videos": [random.choice(videos)],
                "category": {"name": category.name},
                "tags": [{'name': t} for t in tags],
                "location": {
                    "country": city.country,
                    "city": city.city,
                    "latitude": city.latitude + random.uniform(-4, 3) / 100.0,
                    "longitude": city.longitude + random.uniform(-4, 3) / 100.0
                }
            }
            request = Request(HttpRequest())
            request._user = user
            shout = ShoutDetailSerializer(data=shout_data, context={'request': request})
            shout.is_valid(True)
            shout.save()
            self.stdout.write('shout: {}, city: {}'.format(shout_data.get('title'), shout_data.get('location')['city']))

        self.stdout.write('Successfully filled shouts')
