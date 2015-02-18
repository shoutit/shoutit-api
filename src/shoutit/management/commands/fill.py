# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.management.base import NoArgsCommand, CommandError
from shoutit.models import *
from rest_framework.authtoken.models import Token
from shoutit.controllers.user_controller import give_user_permissions
from shoutit.permissions import INITIAL_USER_PERMISSIONS, ACTIVATED_USER_PERMISSIONS
from provider.oauth2.models import Client


class Command(NoArgsCommand):
    help = 'Fill database with required initial data'

    def handle_noargs(self, **options):

        # users
        u1, c1 = User.objects.get_or_create(
            username='syron',
            email='noor.syron@gmail.com',
            is_active=True,
            is_superuser=True,
            is_staff=True,
        )
        u1.first_name = 'Mo'
        u1.last_name = 'Chawich'
        u1.password = "pbkdf2_sha256$12000$LluQpMZvMgfA$9BpmQyVU5dM3Hc20YvVY3K64rsTj/omOQLyfsJuwTCg="
        u1.save()
        t1, c = Token.objects.get_or_create(user=u1)
        t1.delete()
        Token.objects.get_or_create(user=u1, key="1-5fbb04817861540553ca6ecc6d8fb6569f3adb")
        give_user_permissions(None, INITIAL_USER_PERMISSIONS + ACTIVATED_USER_PERMISSIONS, u1)

        u2, c2 = User.objects.get_or_create(
            username='mo',
            email='mo.chawich@gmail.com',
            is_active=True,
            is_superuser=True,
            is_staff=True,
        )
        u2.first_name = 'Mohamad Nour'
        u2.last_name = 'Chawich'
        u2.password = "pbkdf2_sha256$12000$LluQpMZvMgfA$9BpmQyVU5dM3Hc20YvVY3K64rsTj/omOQLyfsJuwTCg="
        u2.save()
        t2, c = Token.objects.get_or_create(user=u2)
        t2.delete()
        Token.objects.get_or_create(user=u2, key="2-5fbb04817861540553ca6ecc6d8fb6569f3adb")
        give_user_permissions(None, INITIAL_USER_PERMISSIONS + ACTIVATED_USER_PERMISSIONS, u2)

        # todo: categories, tags, etc

        # oauth clients
        Client.objects.get_or_create(user=u1, name='shoutit-android', client_id='shoutit-android',
                                     client_secret='319d412a371643ccaa9166163c34387f', client_type=0)

        Client.objects.get_or_create(user=u1, name='shoutit-ios', client_id='shoutit-ios',
                                     client_secret='209b7e713eca4774b5b2d8c20b779d91', client_type=0)

        Client.objects.get_or_create(user=u1, name='shoutit-web', client_id='shoutit-web',
                                     client_secret='0db3faf807534d1eb944a1a004f9cee3', client_type=0)

        Client.objects.get_or_create(user=u1, name='shoutit-test', client_id='shoutit-test',
                                     client_secret='d89339adda874f02810efddd7427ebd6', client_type=0)

        self.stdout.write('Successfully filled initial data')
