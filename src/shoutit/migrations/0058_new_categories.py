# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, transaction

from common.utils import process_tag
from shoutit.models import Category, Tag, Shout


def fill_actions(apps, schema_editor):
    categories = [
        {
            "new": "Fashion & Accessories",
            "old": ["Clothing & Accessories", "Jewelry & Watches"]
        },
        {
            "new": "Electronics",
            "old": ["Camera & Imaging", "Photography"]
        },
        {
            "new": "Toys, Children & Baby",
            "old": ["Baby items", "Toys"]
        },
        {
            "new": "Cars & Motors",
            "old": ["Auto Accessories & Parts", "Boats", "Cars For Sale", "Heavy Vehicles", "Motorcycles"]
        },
        {
            "new": "Home, Furniture & Garden",
            "old": ["Furniture, Home & Garden", "Home Appliances"]
        },
        {
            "new": "Movies, Music & Books",
            "old": ["Books", "DVD & Movies", "Musical Instruments"]
        },
        {
            "new": "Sport, Leisure & Games",
            "old": ["Gaming", "Night Clubs", "Sports Equipment", "Tickets & Vouchers"]
        },
        {
            "new": "Services",
            "old": ["Business & Industrial", "Food and Drinks", "Healthcare", "Hotels", "Restaurants", "Community", "Other"]
        },
        {
            "new": "Computers & Technology",
            "old": ["Computers & Networking", ]
        },
        {
            "new": "Phones & Accessories",
            "old": ["Mobile Phones"]
        },
        {
            "new": "Jobs",
            "old": ["Jobs Wanted"]
        },
        {
            "new": "Real Estate",
            "old": ["Property For Rent", "Property For Sale"]
        }
    ]
    for cat in categories:
        name = cat["new"]
        slug = process_tag(name)
        main_tag = Tag.objects.get_or_create(name=slug)[0]
        # Create the new Category
        category = Category.objects.get_or_create(name=name, slug=slug, main_tag=main_tag)[0]
        old_categories = Category.objects.filter(name__in=cat["old"])
        for old_category in old_categories:
            for tag in old_category.tags.all():
                try:
                    with transaction.atomic():
                        category.tags.add(tag)
                except:
                    pass
        # Update Shouts category
        Shout.objects.filter(category__in=old_categories).update(category=category)


def reverse_fill_actions(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit', '0057_public_chat'),
    ]

    operations = [
        migrations.RunPython(fill_actions, reverse_fill_actions)
    ]
