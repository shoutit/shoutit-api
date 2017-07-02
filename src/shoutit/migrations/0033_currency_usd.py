# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.db.models import F

from shoutit.models import Currency, Item


def set_usd_rates(apps, schema_editor):
    # Get and update currencies
    aed = Currency.objects.get(country='AE', code='AED').update(usd=0.27225)
    usd = Currency.objects.get(country='US', code='USD').update(usd=1.00000)
    eur = Currency.objects.get(country='DE', code='EUR').update(usd=1.14247)
    egp = Currency.objects.get(country='EG', code='EGP').update(usd=0.05444)
    gbp = Currency.objects.get(country='GB', code='GBP').update(usd=1.30278)
    sar = Currency.objects.get(country='SA', code='SAR').update(usd=0.26655)
    kwd = Currency.objects.get(country='KW', code='KWD').update(usd=3.29365)
    qar = Currency.objects.get(country='QA', code='QAR').update(usd=0.26897)
    bhd = Currency.objects.get(country='BH', code='BHD').update(usd=2.65061)
    omr = Currency.objects.get(country='OM', code='OMR').update(usd=2.59687)
    jod = Currency.objects.get(country='JO', code='JOD').update(usd=1.41257)
    sgd = Currency.objects.get(country='SG', code='SGD').update(usd=0.72552)

    # Update items price_usd
    Item.objects.filter(currency=aed).update(price_usd=F('price') * aed.usd)
    Item.objects.filter(currency=eur).update(price_usd=F('price') * eur.usd)
    Item.objects.filter(currency=egp).update(price_usd=F('price') * egp.usd)
    Item.objects.filter(currency=gbp).update(price_usd=F('price') * gbp.usd)
    Item.objects.filter(currency=sar).update(price_usd=F('price') * sar.usd)
    Item.objects.filter(currency=kwd).update(price_usd=F('price') * kwd.usd)
    Item.objects.filter(currency=qar).update(price_usd=F('price') * qar.usd)
    Item.objects.filter(currency=bhd).update(price_usd=F('price') * bhd.usd)
    Item.objects.filter(currency=omr).update(price_usd=F('price') * omr.usd)
    Item.objects.filter(currency=jod).update(price_usd=F('price') * jod.usd)
    Item.objects.filter(currency=sgd).update(price_usd=F('price') * sgd.usd)


def do_nothing(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ('shoutit', '0032_add_new_pdc_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='currency',
            name='usd',
            field=models.FloatField(default=1, help_text='Equivalent to 1 USD'),
        ),
        migrations.AddField(
            model_name='item',
            name='price_usd',
            field=models.BigIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='currency',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='shoutit.Currency'),
        ),
        migrations.RunPython(set_usd_rates, do_nothing)
    ]
