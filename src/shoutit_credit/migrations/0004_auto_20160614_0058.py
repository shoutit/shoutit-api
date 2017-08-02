# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoutit_credit', '0003_shoutpromotion'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompleteProfile',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('shoutit_credit.creditrule',),
        ),
        migrations.CreateModel(
            name='InviteFriends',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('shoutit_credit.creditrule',),
        ),
        migrations.CreateModel(
            name='ListenToFriends',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('shoutit_credit.creditrule',),
        ),
        migrations.CreateModel(
            name='PromoteShouts',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('shoutit_credit.creditrule',),
        ),
        migrations.CreateModel(
            name='ShareShouts',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('shoutit_credit.creditrule',),
        ),
        migrations.AlterField(
            model_name='shoutpromotion',
            name='option',
            field=models.ForeignKey(blank=True, to='shoutit_credit.PromoteShouts', null=True),
        ),
        migrations.AlterField(
            model_name='shoutpromotion',
            name='transaction',
            field=models.OneToOneField(related_name='shout_promotion', null=True, blank=True, to='shoutit_credit.CreditTransaction'),
        ),
    ]
