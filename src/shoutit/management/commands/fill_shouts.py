# -*- coding: utf-8 -*-
"""
Fill database with test shouts from test users
"""
from __future__ import unicode_literals
import random
import time
import logging
from django.core.management.base import BaseCommand
from django.http import HttpRequest
from rest_framework.request import Request
from shoutit.api.v2.serializers import ShoutDetailSerializer
from shoutit.models import User, Category, PredefinedCity
logger = logging.getLogger('shoutit.debug')


class Command(BaseCommand):
    help = 'Fill database with test shouts'
    max_users = 100
    min_shouts = 10
    max_shouts = 100000

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
                user, created = User.objects.get_or_create(username=username, first_name='User',
                                                           last_name=username, email=email,
                                                           is_test=True)
                if created:
                    profile = user.profile
                    city = random.choice(cities)
                    profile.city = city.city
                    profile.country = city.country
                    profile.latitude = city.latitude + random.uniform(-3, 3) / 100.0
                    profile.longitude = city.longitude + random.uniform(-3, 3) / 100.0
                    profile.save()
                logger.debug('Created test user in: {}, lat: {}, lng: {}'.format(user.profile.city, user.profile.latitude, user.profile.longitude))
                users.append(user)

        for i in range(min(max(options.get('num_shouts')[0], self.min_shouts), self.max_shouts)):
            user = random.choice(users)
            type = random.choice(['offer', 'request'])
            category = random.choice(categories)
            city = random.choice(cities)
            tags = random.sample(category.tags.all().values_list('name', flat=1), random.randint(1, min(5, category.tags.count())))
            images = [
                "https://shout-image.static.shoutit.com/opo0928a.jpg",
                "https://shout-image.static.shoutit.com/heic1501a.jpg",
                "https://shout-image.static.shoutit.com/heic0702a.jpg"
            ]
            random.shuffle(images)
            shout_data = {
                "type": type,
                "title": "{0} {1} in {2} at {3:0.0f}".format(category.name, type, city.city, time.time()),
                "text": "".format(" ".join(tags)),
                "price": random.randint(0, 1000),
                "currency": "EUR",
                "images": images,
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

        self.stdout.write('Successfully filled shouts')
