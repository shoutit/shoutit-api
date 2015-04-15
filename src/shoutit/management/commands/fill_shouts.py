# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import random

from django.core.management.base import BaseCommand
from django.http import HttpRequest
from rest_framework.request import Request
import time
from shoutit.api.v2.serializers import TradeDetailSerializer
from shoutit.models import *
from shoutit.controllers.user_controller import give_user_permissions
from shoutit.permissions import INITIAL_USER_PERMISSIONS, ACTIVATED_USER_PERMISSIONS


class Command(BaseCommand):
    help = 'Fill database with test shouts'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('num_shouts', nargs=1, type=int)

    def handle(self, *args, **options):

        users = list(User.objects.filter(username__startswith='test_100'))
        categories = list(Category.objects.all().prefetch_related('tags'))
        cities = PredefinedCity.objects.all()

        # adding 100 test users if we don't have them
        if not len(users) == 1000:
            for i in range(1000):
                username = 'test_' + str(1000000 + i)
                email = username + '@shoutit.com'
                user, _ = User.objects.get_or_create(username=username, first_name='User', last_name=username, email=email)
                give_user_permissions(None, INITIAL_USER_PERMISSIONS + ACTIVATED_USER_PERMISSIONS, user)
                try:
                    user.profile
                except AttributeError:
                    stream = Stream.objects.create(type=0)
                    profile = Profile(user=user, Stream=stream)
                    profile.image = 'https://s3-eu-west-1.amazonaws.com/shoutit-user-image-original/9ca75a6a-fc7e-48f7-9b25-ec71783c28f5-1428689093983.jpg'
                    city = random.choice(cities)
                    profile.city = city.city
                    profile.country = city.country
                    profile.latitude = city.latitude + random.uniform(-3, 3) / 100.0
                    profile.longitude = city.longitude + random.uniform(-3, 3) / 100.0
                    profile.save()
                self.stdout.write('city: {}, lat: {}, lng: {}'.format(user.profile.city, user.profile.latitude, user.profile.longitude))
                users.append(user)

        for i in range(options.get('num_shouts')[0]):
        # for i in range(1000):
            user = random.choice(users)
            type = random.choice(['offer', 'request'])
            category = random.choice(categories)
            city = random.choice(cities)
            tags = [category.main_tag.name] + random.sample(category.tags.all().values_list('name', flat=1), random.randint(1, min(5, category.tags.count())))
            shout_data = {
                "type": type,
                "title": "Test {0} {1:06d}_{2:0.0f} by {3}".format(type, i, time.time(), user.username),
                "text": "This is a test {} from user {}.".format(type, user.username),
                "price": random.randint(0, 1000),
                "currency": "EUR",
                "images": [],
                "videos": [],
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
            shout = TradeDetailSerializer(data=shout_data, context={'request': request})
            shout.is_valid(True)
            shout.save()
            self.stdout.write('shout: {}, city: {}'.format(shout_data.get('title'), shout_data.get('location')['city']))

        self.stdout.write('Successfully filled shouts')
