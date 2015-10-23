# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from common.utils import process_tag
from shoutit.controllers import tag_controller
from shoutit.models import *  # NOQA
from rest_framework.authtoken.models import Token
from provider.oauth2.models import Client


class Command(BaseCommand):
    help = 'Fill database with required initial data'

    def handle(self, *args, **options):

        # users
        u0, _ = User.objects.get_or_create(username='shoutit', email='admin@shoutit.com',
                                           is_activated=True, is_superuser=True, is_staff=True)

        demo, _ = User.objects.get_or_create(username='demo', email='demo@shoutit.com',
                                             is_activated=True, is_test=True)
        demo.first_name = 'Demo'
        demo.last_name = 'Shouter'
        demo.password = "pbkdf2_sha256$20000$ZhCD1pQdaQ3m$gYgjpu0yqoh57CDuPw9q66Gb3e51OeM44ytS+KZs/bc="  # demo123
        demo.save()

        u1, _ = User.objects.get_or_create(username='syron', email='noor.syron@gmail.com',
                                           is_activated=True, is_superuser=True, is_staff=True)
        u1.first_name = 'Nour'
        u1.last_name = 'Syron'
        u1.password = "pbkdf2_sha256$20000$fT380TT4d74W$3CbbfyKvzSBTyBB4F+3/xsciSQkoqRXrVkA/6Xv82NY="
        u1.save()
        Token.objects.filter(user=u1).delete()
        Token.objects.create(user=u1, key="1-5fbb04817861540553ca6ecc6d8fb6569f3adb")

        p1 = u1.profile
        p1.bio = 'Shoutit Master!'
        p1.image = 'https://user-image.static.shoutit.com/mo.jpg'
        p1.gender = 'male'
        p1.save()

        u2, _ = User.objects.get_or_create(username='mo', email='mo.chawich@gmail.com',
                                           is_activated=True, is_superuser=True, is_staff=True)
        u2.first_name = 'Mo'
        u2.last_name = 'Chawich'
        u2.password = "pbkdf2_sha256$20000$fT380TT4d74W$3CbbfyKvzSBTyBB4F+3/xsciSQkoqRXrVkA/6Xv82NY="
        u2.save()

        Token.objects.filter(user=u2).delete()
        Token.objects.create(user=u2, key="2-5fbb04817861540553ca6ecc6d8fb6569f3adb")

        p2 = u2.profile
        p2.bio = 'Shoutit Master 2!'
        p2.image = 'https://user-image.static.shoutit.com/mo.jpg'
        p2.gender = 'male'
        p2.save()

        # Tags, Categories
        categories = [
            ('Cars For Sale', 'cars-for-sale', 'acura', 'alfa-romeo', 'aston-martin',
             'audi', 'bmw', 'bentley', 'bizzarrini',
             'bufori', 'bugatti', 'buick', 'cmc', 'cadillac', 'chevrolet', 'chrysler', 'citroen',
             'daewoo', 'dauihatsu', 'delorean',
             'dodge', 'ferrari', 'fiat', 'fisker', 'ford', 'gmc', 'honda', 'hummer', 'hyundai',
             'infinite', 'isuzu', 'jaguar', 'jeep',
             'kia', 'lamborghini', 'land-rover', 'lexus', 'lincoln', 'lotus', 'mini', 'maserati',
             'maybach', 'mazda', 'mclaren',
             'mercedes-benz', 'mercury', 'mitsubishi', 'nissan', 'peugeot', 'pontiac', 'porsche',
             'smart', 'subaru', 'suzuki', 'tata',
             'toyota', 'volkswagen', 'volvo', 'other-make'),
            ('Auto Accessories & Parts', 'auto-accessories-parts', 'apparel', 'boat-accessories',
             'car-accessories', 'merchandise',
             'motorcycle-accessories'),
            ('Boats', 'boats', 'Fishing-boats', 'racing-boat', 'ski-boat', 'yacht', 'day-boat'),
            ('Heavy Vehicles', 'heavy-vehicles', 'buses', 'Cranes', 'forklifts', 'tankers',
             'trailers', 'trucks'),
            ('Motorcycles', 'motorcycles', 'cruiser-chopper', 'mo-ped', 'off-road', 'scooter',
             'sport-bike', 'touring '),
            ('Property For Sale', 'property-for-sale', 'apartment', 'villa-house', 'commercial',
             'multiple-units', 'land'),
            ('Property For Rent', 'property-for-rent', 'apartment', 'villa-house', 'commercial',
             'short-term-monthly', 'short-term-daily',
             'renat-wanted', 'industrial', 'office', 'retail', 'staff-accomadation', 'rooms'),
            ('Jobs Offered', 'jobs-offered', 'accounting', 'airlines-aviation', 'architecture',
             'art-entertainment', 'automotive',
             'banking-finance', 'beauty', 'business-development', 'business-supplies',
             'construction', 'consulting', 'customer-service',
             'education', 'engineering', 'environmental-services', 'event-management', 'executive',
             'fashion', 'food-beverage',
             'government-adminstration', 'graphic-design', 'hospitality-restaurants',
             'hr-recruitment', 'import-export',
             'industrial-manufacturing', 'information-technology', 'insurance', 'internet',
             'legal-services', 'logistics-distribution',
             'marketing-advertising', 'media', 'medical-healthcare', 'oil-gas-energy',
             'online-media', 'pharmaceuticals',
             'public-relations', 'real-estate', 'research-development', 'retail-consumer-goods',
             'safety-security', 'sales',
             'sports-fitness', 'telecommunications', 'transportation', 'travel-tourism',
             'veterinary-animals', 'warehousing', 'wholesale'),
            ('Jobs Wanted', 'jobs-wanted', 'accounting', 'airlines-aviation', 'architecture',
             'art-entertainment', 'automotive',
             'banking-finance', 'beauty', 'business-development', 'business-supplies',
             'construction', 'consulting', 'customer-service',
             'education', 'engineering', 'environmental-service', 'event-management', 'executive',
             'fashion', 'food-beverage',
             'government-adminstration', 'graphic-design', 'hospitality-restaurants',
             'hr-recruitment', 'import-export',
             'industrial-manufacturing', 'information-technology', 'insurance', 'internet',
             'legal-services', 'logistics-distribution',
             'marketing-advertising', 'media', 'medicial-healthcare', 'oil-gas-energy',
             'online-media', 'pharmaceuticals',
             'public-relations', 'real-estate', 'research-development', 'retail-consumer-goods',
             'safety-security', 'sales',
             'sports-fitness', 'telecommunications', 'transportation', 'travel-tourism',
             'veterinary-animals', 'warehousing', 'wholesale'),
            ('Community', 'Community', 'Artists', 'car-lift', 'charities', 'childcare', 'classes',
             'clubs', 'domestic', 'Education',
             'freelancer', 'misc', 'music', 'news', 'photography', 'services', 'sports',
             'Activities'),
            ('Baby items', 'baby-items', 'baby-gear', 'baby-toys', 'feeding', 'nursery-furniture',
             'stroller', 'car-seat'),
            ('Books', 'books', 'audiobooks', 'book-accessories', 'children-books',
                'digital/E-books',
                'fiction', 'nonfiction', 'textbooks'),
            ('Business & Industrial', 'business-industrial', 'agriculture-forestry',
             'business-for-sale', 'commercial-printing',
             'copy-machines', 'construction', 'electrical-equipment', 'food-beverage',
             'healthcare-lab', 'industrial-supplies',
             'manufacturing', 'office-furniture', 'office-equipment', 'packing-shipping',
             'retail-services'),
            ('Camera & Imaging', 'camera-imaging', 'binoculars', 'telescope',
             'camcorder-accessories', 'digital-camera',
             'digital-photo-frames', 'film-camera', 'lense', 'filter-lighting',
             'proffesional-equipment', 'tripods-stands'),
            ('Clothing & Accessories', 'clothing-accessories', 'clothing', 'costumes-uniforms',
             'fragrance', 'handbag', 'wallet', 'luggage',
             'mens-accessories', 'shoes-footwear', 'vintage', 'highend-clothing', 'wedding-apparel',
             'womens-accessories'),
            ('Collectibles', 'collectibles', 'antiques', 'art', 'decorations', 'memorabilia',
             'pens-writing-instrument', 'artifacts'),
            ('Computers & Networking', 'computers-networking', 'accessories',
                'computer-components', 'computers', 'networking-communication',
                'software', 'monitors', 'printers'),
            ('DVD & Movies', 'dvd-movies', 'dvd', 'digital', 'vhs'),
            ('Electronics', 'electronics', 'car-electronics', 'dvd-home-theater',
             'electronic-accessories', 'gadgets', 'home-audio',
             'turntables', 'mp3-players', 'satellite-cable-tv', 'satellite-radio', 'tv'),
            ('Furniture, Home & Garden', 'furniture-home-garden', 'curtains-blinds', 'furniture',
             'garden-outdoor', 'home-accessories',
             'lighting-fans', 'rugs-carpets', 'tools-home-improvement'),
            ('Gaming', 'gaming', 'gaming-accessories', 'gaming-merchandise', 'gaming-system',
             'video-games'),
            ('Home Appliances', 'outdoor-appliances', 'kitchen-appliances',
                'bathroom-appliances '),
            ('Hotels', 'hotels', '5-star', '4-star', '3-star', '2-star', 'hotel-apartments'),
            ('Jewelry & Watches', 'jewelry-watches', 'diamonds-gems', 'mens-jewelry', 'watches',
             'womens-jewelry'),
            ('Mobile Phones', 'mobile-phones', 'pda'),
            ('Musical Instruments', 'musical-instruments', 'guitars', 'percussion', 'pianos',
             'keyboards', 'organs', 'string-instruments',
             'wind-instruments'),
            ('Pets', 'pets', 'dogs', 'cats'),
            ('Sports Equipment', 'sports-equipment', 'camping-hiking', 'cycling',
             'execerise-equipment', 'golf', 'indoor-sports',
             'team-sports', 'tennis', 'water-sports'),
            ('Tickets & Vouchers', 'tickets-vouchers', 'concerts', 'events', 'movies',
             'sporting-events', 'theater', 'travel'),
            ('Toys', 'toys', 'action-figures', 'toy-vehicles', 'classic-vintage-toys',
             'dolls-stuffed-animals', 'educational-toys',
             'electronic toys', 'remote-control-toys', 'Games-puzzles', 'hobbies', 'outdoor-toys',
             'structures'),
            ('Services', 'services', 'automotive-services', 'bank-services', 'beauty-services',
             'computer-services', 'creative-services',
             'event-services', 'financial-services', 'fitness-services', 'household-services',
             'labor-moving services',
             'landscaping-services', 'legal-services', 'marine-services', 'massage-services',
             'pet-services', 'real-estate-services',
             'taxi-services', 'travel-vacation-services', 'Private-car-services',
             'limousine-services', 'rent-car-service',
             'restaurant-delivery', 'grocery-delivery'),
            ('Restaurants', 'restaurants', 'breakfast', 'lunch', 'dinner', 'buffet', 'fine-dining',
             'american', 'arabic', 'asian', 'bakery',
             'chinese', 'continental', 'fast-food', 'French', 'indian', 'international', 'iranian',
             'italian', 'lebanese', 'pakistani',
             'pizza', 'seafood', 'steaks', 'sushi', 'thai', 'turkish', 'vegetarian'),
            ('Other', 'other'),
            ('Food and Drinks', 'food-drink', 'drink', 'tea')
        ]

        for item in categories:
            category = item[0]
            main_tag = item[1]
            tags = item[1:]

            main_tag = tag_controller.get_or_create_tag(main_tag)
            category, _ = Category.objects.get_or_create(name=category)
            category.main_tag = main_tag
            category.slug = process_tag(category.name)
            category.save()
            for tag in tags:
                tag = tag_controller.get_or_create_tag(tag)
                if tag:
                    try:
                        category.tags.add(tag)
                    except:
                        pass

        # oauth clients
        Client.objects.get_or_create(user=u0, name='shoutit-android', client_id='shoutit-android',
                                     client_secret='319d412a371643ccaa9166163c34387f',
                                     client_type=0)

        Client.objects.get_or_create(user=u0, name='shoutit-ios', client_id='shoutit-ios',
                                     client_secret='209b7e713eca4774b5b2d8c20b779d91',
                                     client_type=0)

        Client.objects.get_or_create(user=u0, name='shoutit-web', client_id='shoutit-web',
                                     client_secret='0db3faf807534d1eb944a1a004f9cee3',
                                     client_type=0)

        Client.objects.get_or_create(user=u0, name='shoutit-test', client_id='shoutit-test',
                                     client_secret='d89339adda874f02810efddd7427ebd6',
                                     client_type=0)

        # pre defined cities
        cities = [
            ('Abu Dhabi', 'AE', 24.3865481, 54.5599079, True),
            ('Dubai', 'AE', 25.1993957, 55.2738326, True),
            ('Sharjah', 'AE', 25.328435, 55.512258, True),
            ('Ajman', 'AE', 25.3994029, 55.5305745, True),

            ('Berlin', 'DE', 52.522594, 13.402388, True),
            ('Hamburg', 'DE', 53.558572, 9.9278215, True),
            ('Munich', 'DE', 48.1549107, 11.5418357, True),
            ('Ingolstadt', 'DE', 48.7533744, 11.3796516, True),
            ('Cologne', 'DE', 50.957245, 6.9673223, True),
            ('Aachen', 'DE', 50.7738792, 6.0844869, True),
        ]
        for t in cities:
            PredefinedCity.objects.get_or_create(city=t[0], country=t[1], latitude=t[2], longitude=t[3], approved=t[4])

        # currencies
        Currency.objects.get_or_create(country='AE', code='AED', name='Dirham')
        Currency.objects.get_or_create(country='US', code='USD', name='Dollar')
        Currency.objects.get_or_create(country='DE', code='EUR', name='Euro')
        Currency.objects.get_or_create(country='EG', code='EGP', name='Pound')
        Currency.objects.get_or_create(country='GB', code='GBP', name='Pound')
        Currency.objects.get_or_create(country='SA', code='SAR', name='Riyal')
        Currency.objects.get_or_create(country='KW', code='KWD', name='Riyal')
        Currency.objects.get_or_create(country='QA', code='QAR', name='Riyal')
        Currency.objects.get_or_create(country='BH', code='BHD', name='Riyal')
        Currency.objects.get_or_create(country='OM', code='OMR', name='Riyal')
        Currency.objects.get_or_create(country='JO', code='JOD', name='Riyal')

        self.stdout.write('Successfully filled initial data')
