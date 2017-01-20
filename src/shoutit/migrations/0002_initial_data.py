# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from provider.oauth2.models import Client

from provider.constants import CONFIDENTIAL


def fill_initial_data(apps, schema_editor):
    # oAuth Clients
    # bulk_create doesn't work here as the `modified` field is not nullable
    Client.objects.create(name='shoutit-android', client_id='shoutit-android',
                          client_secret='319d412a371643ccaa9166163c34387f',
                          client_type=CONFIDENTIAL)

    Client.objects.create(name='shoutit-ios', client_id='shoutit-ios',
                          client_secret='209b7e713eca4774b5b2d8c20b779d91',
                          client_type=CONFIDENTIAL)

    Client.objects.create(name='shoutit-web', client_id='shoutit-web',
                          client_secret='0db3faf807534d1eb944a1a004f9cee3',
                          client_type=CONFIDENTIAL)

    Client.objects.create(name='shoutit-test', client_id='shoutit-test',
                          client_secret='d89339adda874f02810efddd7427ebd6',
                          client_type=CONFIDENTIAL)

    # Categories and Tags
    Category = apps.get_model('shoutit', 'Category')
    Tag = apps.get_model('shoutit', 'Tag')

    categories = [
        ('Cars & Motors', 'cars-motors'),
        ('Collectibles', 'collectibles'),
        ('Computers & Technology', 'computers-technology'),
        ('Electronics', 'electronics'),
        ('Fashion & Accessories', 'fashion-accessories'),
        ('Home, Furniture & Garden', 'home-furniture-garden'),
        ('Jobs', 'jobs'),
        ('Movies, Music & Books', 'movies-music-books'),
        ('Other', 'other'),
        ('Pets', 'pets'),
        ('Phones & Accessories', 'phones-accessories'),
        ('Real Estate', 'real-estate'),
        ('Services', 'services'),
        ('Sport, Leisure & Games', 'sport-leisure-games'),
        ('Beauty & Health', 'beauty-health'),
        ('Hotels & Restaurants', 'hotels-restaurants'),
        ('Groceries & Beverages', 'groceries-beverages'),
    ]

    Category.objects.bulk_create(
        [Category(name=c[0], slug=c[1]) for c in categories]
    )

    Tag.objects.bulk_create(
        [Tag(name=c[1]) for c in categories]
    )

    # Currencies
    Currency = apps.get_model('shoutit', 'Currency')
    Currency.objects.bulk_create([
        Currency(country='AE', code='AED', name='Dirham'),
        Currency(country='US', code='USD', name='Dollar'),
        Currency(country='DE', code='EUR', name='Euro'),
        Currency(country='EG', code='EGP', name='Pound'),
        Currency(country='GB', code='GBP', name='Pound'),
        Currency(country='SA', code='SAR', name='Riyal'),
        Currency(country='KW', code='KWD', name='Dinar'),
        Currency(country='QA', code='QAR', name='Rial'),
        Currency(country='BH', code='BHD', name='Dinar'),
        Currency(country='OM', code='OMR', name='Rial'),
        Currency(country='JO', code='JOD', name='Dinar'),
    ])


def remove_initial_data(apps, schema_editor):

    Client.objects.all().delete()

    Category = apps.get_model('shoutit', 'Category')
    Category.objects.all().delete()

    Tag = apps.get_model('shoutit', 'Tag')
    Tag.objects.all().delete()

    Currency = apps.get_model('shoutit', 'Currency')
    Currency.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit', '0001_initial'),
        ('provider', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fill_initial_data, remove_initial_data)
    ]
