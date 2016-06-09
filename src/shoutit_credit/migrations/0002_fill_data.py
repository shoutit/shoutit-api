# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from shoutit_credit.models import CreditRule, CREDIT_OUT, CREDIT_IN, PromoteLabel


def fill_data(apps, schema_editor):
    # In rules
    CreditRule.objects.create(transaction_type=CREDIT_IN, type='complete_profile', name="Complete your Profile")
    CreditRule.objects.create(transaction_type=CREDIT_IN, type='invite_friends', name="Inviting friends")
    CreditRule.objects.create(transaction_type=CREDIT_IN, type='listen_to_friends', name="Listening to friends")
    CreditRule.objects.create(transaction_type=CREDIT_IN, type='share_shouts', name="Share Shouts")

    # Promote labels
    premium = PromoteLabel.objects.create(name="PREMIUM", rank=1, description="Your shout will be highlighted in all searches.",
                                          color="#FFFFD700", bg_color="#26FFD700")
    top = PromoteLabel.objects.create(name="TOP", rank=2, description="Your shout will appear on top of search results.",
                                      color="#FFC0C0C0", bg_color="#26C0C0C0")
    top_premium = PromoteLabel.objects.create(name="TOP PREMIUM", rank=3, description="Your shout will be highlighted and appear on top of all searches.",
                                              color="#FFFFD700", bg_color="#26FFD700")

    # Out rules
    ps1 = {'name': "PREMIUM HIGHLIGHT", 'description': "Your shout will be highlighted in all searches."}
    ps1_options = {'label_id': premium.pk, 'days': None, 'credits': 3, 'rank': 1}
    CreditRule.objects.create(transaction_type=CREDIT_OUT, type='promote_shouts', options=ps1_options, **ps1)

    ps2 = {'name': "TOP RESULTS", 'description': "Your shout will appear on top of search results for 3 days."}
    ps2_options = {'label_id': top.pk, 'days': 3, 'credits': 3, 'rank': 2}
    CreditRule.objects.create(transaction_type=CREDIT_OUT, type='promote_shouts', options=ps2_options, **ps2)

    ps3 = {'name': "TOP & PREMIUM", 'description': "Your shout will be highlighted and appear on top of all searches for 5 days."}
    ps3_options = {'label_id': top_premium.pk, 'days': 5, 'credits': 5, 'rank': 3}
    CreditRule.objects.create(transaction_type=CREDIT_OUT, type='promote_shouts', options=ps3_options, **ps3)

    ps4 = {'name': "TOP & PREMIUM", 'description': "Your shout will be highlighted and appear on top of all searches for 10 days."}
    ps4_options = {'label_id': top_premium.pk, 'days': 10, 'credits': 10, 'rank': 4}
    CreditRule.objects.create(transaction_type=CREDIT_OUT, type='promote_shouts', options=ps4_options, **ps4)


def remove_data(apps, schema_editor):
    CreditRule.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_credit', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fill_data, remove_data)
    ]
