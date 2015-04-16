# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from shoutit.controllers import tag_controller
from shoutit.models import *
from rest_framework.authtoken.models import Token
from shoutit.controllers.user_controller import give_user_permissions
from shoutit.permissions import INITIAL_USER_PERMISSIONS, ACTIVATED_USER_PERMISSIONS
from provider.oauth2.models import Client


class Command(BaseCommand):
    help = 'Fill database with required initial data'

    def handle(self, *args, **options):

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
        try:
            p1 = u1.profile
        except AttributeError:
            p1 = Profile(user=u1)

        p1.Bio = 'Shoutit Master!'
        p1.image = 'http://2ed106c1d72e039a6300-f673136b865c774b4127f2d581b9f607.r83.cf5.rackcdn.com/1NHUqCeh94NaWb8hlu74L7.jpg'
        p1.Sex = True
        p1.city = 'Dubai'
        p1.country = 'AE'
        p1.latitude = 25.1993957
        p1.longitude = 55.2738326
        p1.save()

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
        try:
            p2 = u2.profile
        except AttributeError:
            p2 = Profile(user=u2)

        p2.Bio = 'Shoutit Master 2!'
        p2.image = 'http://2ed106c1d72e039a6300-f673136b865c774b4127f2d581b9f607.r83.cf5.rackcdn.com/1NHUqCeh94NaWb8hlu74L7.jpg'
        p2.Sex = True
        p2.city = 'Dubai'
        p2.country = 'AE'
        p2.latitude = 25.1593957
        p2.longitude = 55.2338326
        p2.save()

        # Tags, Categories
        categories = [
            ('New Cars For Sale', 'new-car-for-sale', 'acura', 'alfa-Romeo', 'aston-martin', 'audi', 'bmw', 'bentley', 'bizzarrini',
             'bufori', 'bugatti', 'buick', 'cmc', 'cadillac', 'chevrolet', 'chrysler', 'citroen', 'daewoo', 'dauihatsu', 'delorean',
             'dodge', 'ferrari', 'fiat', 'fisker', 'ford', 'gmc', 'honda', 'hummer', 'hyundai', 'infinite', 'isuzu', 'jaguar', 'jeep',
             'kia', 'lamborghini', 'Land-rover', 'lexus', 'lincoln', 'lotus', 'mini', 'maserati', 'maybach', 'mazda', 'mclaren',
             'Mercedes-benz', 'mercury', 'mitsubishi', 'nissan', 'peugeot', 'pontiac', 'porsche', 'smart', 'subaru', 'suzuki', 'tata',
             'toyota', 'volkswagen', 'volvo', 'other-make'),
            ('Used Cars For Sale', 'used-car-for-sale', 'acura', 'alfa-romeo', 'aston-martin', 'audi', 'bmw', 'bentley', 'bizzarrini',
             'bufori', 'bugatti', 'buick', 'cmc', 'cadillac', 'chevrolet', 'chrysler', 'citroen', 'daewoo', 'dauihatsu', 'delorean',
             'dodge', 'ferrari', 'fiat', 'fisker', 'ford', 'gmc', 'honda', 'hummer', 'hyundai', 'infinite', 'isuzu', 'jaguar', 'jeep',
             'kia', 'lamborghini', 'land-rover', 'lexus', 'lincoln', 'lotus', 'mini', 'maserati', 'maybach', 'mazda', 'mclaren',
             'mercedes-benz', 'mercury', 'mitsubishi', 'nissan', 'peugeot', 'pontiac', 'porsche', 'smart', 'subaru', 'suzuki', 'tata',
             'toyota', 'volkswagen', 'volvo', 'other-make'),
            ('Auto Accessories & Parts', 'auto-accessories-parts', 'apparel', 'boat-accessories', 'car-accessories', 'merchandise',
             'motorcycle-accessories'),
            ('Boats', 'boats', 'Fishing-boats', 'racing-boat', 'ski-boat', 'yacht', 'day-boat'),
            ('Heavy Vehicles', 'heavy-vehicles', 'buses', 'Cranes', 'forklifts', 'tankers', 'trailers', 'trucks'),
            ('Motorcycles', 'motorcycles', 'cruiser-chopper', 'mo-ped', 'off-road', 'scooter', 'sport-bike', 'touring '),
            ('Property For Sale', 'property-for-sale', 'apartment', 'villa-house', 'commercial', 'multiple-units', 'land'),
            ('Property For Rent', 'property-for-rent', 'apartment', 'villa-house', 'commercial', 'short-term-monthly', 'short-term-daily',
             'renat-wanted', 'industrial', 'office', 'retail', 'staff-accomadation', 'rooms'),
            ('Jobs Offered', 'Jobs-offered', 'accounting', 'airlines-aviation', 'architecture', 'art-entertainment', 'automotive',
             'banking-finance', 'beauty', 'business-development ', 'business-supplies', 'construction', 'consulting', 'customer-service',
             'education', 'engineering', 'environmental-services', 'event-management', 'executive', 'fashion', 'food-beverage ',
             'government-adminstration', 'graphic-design', 'hospitality-restaurants', 'hr-recruitment ', 'import-export',
             'industrial-manufacturing ', 'information-technology ', 'insurance', 'internet', 'legal-services', 'logistics-distribution',
             'marketing-advertising ', 'media', 'medical-healthcare', 'oil-gas-energy', 'online-media', 'pharmaceuticals',
             'public-relations', 'real-estate ', 'research-development ', 'retail-consumer-goods', 'safety-security', 'sales',
             'sports-fitness', 'telecommunications', 'transportation', 'travel-tourism', 'veterinary-animals', 'warehousing', 'wholesale'),
            ('Jobs Wanted ', 'Jobs-wanted', 'accounting', 'airlines-aviation', 'architecture', 'art-entertainment', 'automotive',
             'banking-finance', 'beauty', 'business-development', 'business-supplies', 'construction', 'consulting', 'customer-service',
             'education', 'engineering', 'environmental-service', 'event-management', 'executive', 'fashion', 'food-beverage',
             'government-adminstration', 'graphic-design', 'hospitality-restaurants', 'hr-recruitment', 'import-export',
             'industrial-manufacturing', 'information-technology ', 'insurance ', 'internet', 'legal-services', 'logistics-distribution',
             'marketing-advertising ', 'media', 'medicial-healthcare', 'oil-gas-energy', 'online-media', 'pharmaceuticals',
             'public-relations', 'real-estate', 'research-development ', 'retail-consumer-goods', 'safety-security', 'sales',
             'sports-fitness', 'telecommunications', 'transportation', 'travel-tourism', 'veterinary-animals', 'warehousing ', 'wholesale'),
            ('Community', 'Community', 'Artists', 'car-lift', 'charities', 'childcare', 'classes', 'clubs ', 'domestic', 'Education',
             'freelancer', 'misc ', 'music ', 'news', 'photography', 'services', 'sports', 'Activities'),
            ('Baby items', 'baby-items', 'baby-gear', 'baby-toys', 'feeding', 'nursery-furniture', 'stroller', 'car-seat'),
            ('Books', 'books', 'audiobooks', 'book-accessories', 'children-books', 'digital/E-books', 'fiction', 'nonfiction', 'textbooks'),
            ('Business & Industrial', 'business-industrial', 'agriculture-forestry', 'business-for-sale', 'commercial-printing',
             'copy-machines', 'construction', 'electrical-equipment', 'food-beverage', 'healthcare-lab', 'industrial-supplies',
             'manufacturing', 'office-furniture', 'office-equipment', 'packing-shipping', 'retail-services'),
            ('Camera & Imaging', 'camera-imaging', 'binoculars', 'telescope', 'camcorder-accessories', 'digital-camera',
             'digital-photo-frames', 'film-camera', 'lense', 'filter-lighting', 'proffesional-equipment', 'tripods-stands'),
            ('Clothing & Accessories', 'clothing-accessories', 'clothing', 'costumes-uniforms', 'fragrance', 'handbag', 'wallet', 'luggage',
             'mens-accessories', 'shoes-footwear', 'vintage', 'highend-clothing', 'wedding-apparel', 'womens-accessories'),
            ('Collectibles', 'collectibles', 'antiques', 'art', 'decorations', 'memorabilia', 'pens-writing-instrument', 'artifacts'),
            (
            'Computers & Networking', 'computers-networking', 'accessories', 'computer-components', 'computers', 'networking-communication',
            'software ', 'monitors', 'printers'),
            ('DVD & Movies', 'dvd-movies', 'dvd', 'digital', 'vhs'),
            ('Electronics', 'electronics', 'car-electronics', 'dvd-home-theater', 'electronic-accessories', 'gadgets', 'home-audio',
             'turntables', 'mp3-players', 'satellite-cable-tv', 'satellite-radio', 'tv'),
            ('Furniture, Home & Garden', 'furniture-home-garden', 'curtains-blinds', 'furniture', 'garden-outdoor', 'home-accessories',
             'lighting-fans', 'rugs-carpets', 'tools-home-improvement'),
            ('Gaming ', 'gaming', 'gaming-accessories', 'gaming-merchandise', 'gaming-system', 'video-games'),
            ('Home Appliances', 'outdoor-appliances', 'kitchen-appliances ', 'bathroom-appliances '),
            ('Hotels', 'hotels', '5-star', '4-star', '3-star', '2-star', 'hotel-apartments'),
            ('Jewelry & Watches', 'jewelry-watches', 'diamonds-gems', 'mens-jewelry', 'watches', 'womens-jewelry'),
            ('Mobile Phones & PDA', 'mobile-phones-pda', 'mobile-phones', 'pda'),
            ('Musical Instruments', 'musical-instruments', 'guitars', 'percussion', 'pianos', 'keyboards', 'organs', 'string-instruments',
             'wind-instruments'),
            ('Pets', 'pets', 'dogs', 'cats'),
            ('Sports Equipment ', 'sports-equipment', 'camping-hiking', 'cycling', 'execerise-equipment ', 'golf', 'indoor-sports',
             'team-sports', 'tennis', 'water-sports'),
            ('Tickets & Vouchers', 'tickets-vouchers', 'concerts', 'events ', 'movies', 'sporting-events', 'theater', 'travel'),
            ('Toys', 'toys', 'action-figures', 'toy-vehicles ', 'classic-vintage-toys', 'dolls-stuffed-animals', 'educational-toys',
             'electronic toys', 'remote-control-toys', 'Games-puzzles', 'hobbies', 'outdoor-toys', 'structures'),
            ('Services', 'services', 'automotive-services', 'bank-services', 'beauty-services', 'computer-services', 'creative-services',
             'event-services', 'financial-services', 'fitness-services', 'household-services', 'labor-moving services',
             'landscaping-services', 'legal-services', 'marine-services', 'massage-services', 'pet-services', 'real-estate-services',
             'taxi-services', 'travel-vacation-services', 'Private-car-services', 'limousine-services', 'rent-car-service',
             'restaurant-delivery', 'grocery-delivery'),
            ('Restaurants', 'restaurants', 'breakfast', 'lunch', 'dinner', 'buffet', 'fine-dining', 'american', 'arabic', 'asian', 'bakery',
             'chinese', 'continental', 'fast-food', 'French', 'indian', 'international', 'iranian', 'italian', 'lebanese', 'pakistani',
             'pizza', 'seafood', 'steaks', 'sushi', 'thai', 'turkish', 'vegetarian'),
            ('Other', 'other')
        ]

        for item in categories:
            category = item[0]
            main_tag = item[1]
            tags = item[1:]

            main_tag = tag_controller.get_or_create_tag(main_tag)
            category, _ = Category.objects.get_or_create(name=category)
            category.main_tag = main_tag
            category.save()
            for tag in tags:
                tag = tag_controller.get_or_create_tag(tag)
                if tag:
                    try:
                        category.tags.add(tag)
                    except:
                        pass

        # oauth clients
        Client.objects.get_or_create(user=u1, name='shoutit-android', client_id='shoutit-android',
                                     client_secret='319d412a371643ccaa9166163c34387f', client_type=0)

        Client.objects.get_or_create(user=u1, name='shoutit-ios', client_id='shoutit-ios',
                                     client_secret='209b7e713eca4774b5b2d8c20b779d91', client_type=0)

        Client.objects.get_or_create(user=u1, name='shoutit-web', client_id='shoutit-web',
                                     client_secret='0db3faf807534d1eb944a1a004f9cee3', client_type=0)

        Client.objects.get_or_create(user=u1, name='shoutit-test', client_id='shoutit-test',
                                     client_secret='d89339adda874f02810efddd7427ebd6', client_type=0)

        # pre defined cities
        PredefinedCity.objects.get_or_create(city='Dubai', city_encoded='dubai', country='AE',
                                             latitude=25.1993957, longitude=55.2738326, Approved=True)
        PredefinedCity.objects.get_or_create(city='Aachen', city_encoded='aachen', country='DE',
                                             latitude=50.7738792, longitude=6.0844869, Approved=True)
        PredefinedCity.objects.get_or_create(city='Berlin', city_encoded='berlin', country='DE',
                                             latitude=52.522594, longitude=13.402388, Approved=True)

        # currencies
        Currency.objects.get_or_create(country='AE', code='AED', name='Dirham')
        Currency.objects.get_or_create(country='US', code='USD', name='Dollar')
        Currency.objects.get_or_create(country='DE', code='EUR', name='Euro')

        self.stdout.write('Successfully filled initial data')
