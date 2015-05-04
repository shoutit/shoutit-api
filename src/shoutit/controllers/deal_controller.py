from __future__ import unicode_literals
import StringIO
from datetime import datetime
import urllib2

from django.core.exceptions import ObjectDoesNotExist
from geraldo import Report, ReportBand, DetailBand, SystemField, Label, ObjectValue, Image, Rect
from reportlab.lib.colors import orange
from geraldo.utils import cm, BAND_WIDTH, TA_RIGHT
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from geraldo.generators import PDFGenerator
import reportlab.graphics.barcode
from PIL.Image import open as image_open

from shoutit.models import DealBuy, Voucher, Shout
from shoutit.controllers import event_controller, item_controller


def ShoutDeal(name, description, price, images, currency, tags, expiry_date, min_buyers, max_buyers, original_price, business_profile,
              country, city, valid_from=None, valid_to=None):
    # currency = Currency.objects.get(code__iexact = currency)
    item = item_controller.create_item(name=name, price=price, description=description, currency=currency, images=images)

    deal = Deal(
        MinBuyers=min_buyers,
        MaxBuyers=max_buyers,
        OriginalPrice=original_price,
        item=item,
        country=country,
        city=city
    )
    deal.text = description
    deal.type = POST_TYPE_DEAL
    deal.user = business_profile.user
    deal.expiry_date = expiry_date
    deal.ValidFrom = valid_from
    deal.ValidTo = valid_to
    deal.save()

    stream = business_profile.stream

    stream.add_post(deal)

    for tag in shoutit.controllers.tag_controller.get_or_create_tags(tags, deal.user):
        tag.stream.add_post(deal)

    event_controller.register_event(business_profile.user, EVENT_TYPE_POST_DEAL, deal)
    return deal


def GetConcurrentDeals(business_profile):
    return Deal.objects.get_valid_deals().filter(user=business_profile.user, IsClosed=False)


def get_image_for_voucher(voucher_band):

    image_url = voucher_band.instance.DealBuy.Deal.item.get_first_image()
    if image_url:
        img_file = urllib2.urlopen(image_url)
        return image_open(StringIO.StringIO(img_file.read()))
    return None


def get_qr_for_voucher(voucher_band):
    from common.PyQRNative import QRCode
    from common.PyQRNative import QRErrorCorrectLevel

    qr = QRCode(3, QRErrorCorrectLevel.L)
    qr.addData(voucher_band.instance.code)
    qr.make()
    return qr.makeImage()


def get_barcode_for_voucher(voucher_band):

    buffer = StringIO.StringIO()
    buffer.write(
        reportlab.graphics.barcode.createBarcodeImageInMemory('Code128', value=voucher_band.instance.code, format='png', height=6 * cm,
                                                              width=24 * cm))
    buffer.seek(0)
    return image_open(buffer)


def get_id_for_voucher(widget, voucher_band):
    if not hasattr(widget.report, 'record_id_in_report'):
        widget.report.record_id_in_report = 0
    if not hasattr(widget.instance, 'record_id_in_report'):
        widget.report.record_id_in_report += 1
        widget.instance.record_id_in_report = widget.report.record_id_in_report
    return '%d' % widget.instance.record_id_in_report


def get_validity_for_deal(widget, band):
    result = ''
    if widget.instance.DealBuy.Deal.ValidFrom:
        result += 'Valid from %s' % widget.instance.DealBuy.Deal.ValidFrom.strftime('%d/%m/%Y %H:%M:%S%z')
    if widget.instance.DealBuy.Deal.ValidTo:
        if widget.instance.DealBuy.Deal.ValidFrom:
            result += ' to %s' % widget.instance.DealBuy.Deal.ValidTo.strftime('%d/%m/%Y %H:%M:%S%z')
        else:
            result += 'Valid to %s' % widget.instance.DealBuy.Deal.ValidTo.strftime('%d/%m/%Y %H:%M:%S%z')
    return result


class VoucherReport(Report):
    class band_page_header(ReportBand):
        height = 1.0 * cm
        elements = [
            SystemField(expression='%(report_title)s', top=0 * cm, left=0, width=BAND_WIDTH,
                        style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
            SystemField(expression=u'Page %(page_number)d of %(page_count)d', top=0 * cm, width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
        ]
        borders = {'bottom': True}

    class band_detail(ReportBand):
        height = 25.1 * cm
        elements = [
            Rect(left=00.00 * cm, top=00.25 * cm, width=06.0 * cm, height=02.50 * cm, fill=True, stroke=False, fill_color=orange),  #Logo
            Label(get_value=lambda widget, band: widget.instance.DealBuy.Deal.item.name,
                  style={'wordWrap': True, 'alignment': TA_JUSTIFY, 'fontName': 'Helvetica-Bold', 'fontSize': 28},
                  left=00.00 * cm, top=03.40 * cm, width=12.0 * cm, height=02.50 * cm),  #Deal Name
            Label(get_value=get_validity_for_deal,
                  style={'wordWrap': True, 'alignment': TA_JUSTIFY, 'fontName': 'Helvetica-Bold', 'fontSize': 10},
                  left=00.00 * cm, top=06.10 * cm, width=12.0 * cm, height=01.00 * cm),  #Validity
            Image(left=00.33 * cm, top=07.60 * cm, width=06.0 * cm, height=06.00 * cm, get_image=get_image_for_voucher),  #Image
            Rect(left=00.00 * cm, top=20.00 * cm, width=18.5 * cm, height=05.00 * cm, fill=True, stroke=False, fill_color=orange),
            #How To Use

            Image(left=14.55 * cm, top=00.50 * cm, width=06.0 * cm, height=06.00 * cm, get_image=get_qr_for_voucher),  #QR
            Image(left=12.50 * cm, top=03.70 * cm, width=13.0 * cm, height=02.50 * cm, get_image=get_barcode_for_voucher),  #Barcode
            Label(get_value=lambda widget, band: widget.instance.code,
                  style={'wordWrap': True, 'alignment': TA_CENTER, 'fontName': 'Helvetica-Bold', 'fontSize': 18},
                  left=13.00 * cm, top=05.20 * cm, width=06.5 * cm, height=00.70 * cm),  #Code
            # price
            # Label(get_value=lambda widget, band: price(widget.instance.DealBuy.Deal.item.price,
            #                                            widget.instance.DealBuy.Deal.item.currency.code),
            #       style={'wordWrap': True, 'alignment': TA_CENTER, 'fontName': 'Helvetica-Bold', 'fontSize': 24},
            #       left=13.20 * cm, top=06.20 * cm, width=05.5 * cm, height=02.50 * cm, fill=True, stroke=False, fill_color=orange),  #Worth
            Label(get_value=lambda widget, band: widget.instance.DealBuy.Deal.text,
                  style={'wordWrap': True, 'alignment': TA_JUSTIFY, 'fontName': 'Helvetica', 'fontSize': 14},
                  left=06.95 * cm, top=09.00 * cm, width=11.5 * cm, height=10.50 * cm),  #Description
        ]

    class band_page_footer(ReportBand):
        height = 0.5 * cm
        elements = [
            Label(text='Shoutit Deals', top=0.1 * cm),
            SystemField(expression='Printed in %(now:%Y, %b %d)s at %(now:%H:%M)s', top=0.1 * cm, width=BAND_WIDTH,
                        style={'alignment': TA_RIGHT}),
        ]
        borders = {'top': True}


class BuyersReport(Report):
    class band_detail(DetailBand):
        height = 2.4 * cm
        elements = [
            Label(left=0.5 * cm, get_value=get_id_for_voucher, top=1 * cm),
            ObjectValue(expression='Code', left=2.5 * cm, top=1 * cm),
            Image(left=8 * cm, top=0.1 * cm, width=4 * cm, height=4 * cm, get_image=get_qr_for_voucher),
            Image(left=10.5 * cm, top=0.5 * cm, width=16 * cm, height=2 * cm, get_image=get_barcode_for_voucher),
        ]
        borders = {'bottom': True}

    class band_page_header(ReportBand):
        height = 1.3 * cm
        elements = [
            SystemField(expression='%(report_title)s', top=0.1 * cm, left=0, width=BAND_WIDTH,
                        style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
            SystemField(expression=u'Page %(page_number)d of %(page_count)d', top=0.1 * cm, width=BAND_WIDTH,
                        style={'alignment': TA_RIGHT}),
            Label(text="ID", top=0.8 * cm, left=0.5 * cm),
            Label(text="Code", top=0.8 * cm, left=2.5 * cm),
            Label(text="QR Code", top=0.8 * cm, left=8 * cm),
            Label(text="Barcode", top=0.8 * cm, left=12.5 * cm),
        ]
        borders = {'bottom': True}

    class band_page_footer(ReportBand):
        height = 0.5 * cm
        elements = [
            Label(text='Shoutit Deals', top=0.1 * cm),
            SystemField(expression='Printed in %(now:%Y, %b %d)s at %(now:%H:%M)s', top=0.1 * cm, width=BAND_WIDTH,
                        style={'alignment': TA_RIGHT}),
        ]
        borders = {'top': True}

    class band_summary(ReportBand):
        height = 0.5 * cm
        elements = [
            Label(text='Total Vouchers:'),
            ObjectValue(expression='count(Code)', left=5 * cm),
        ]
        borders = {'top': True}


def GenerateVoucherDocument(deal_buy):
    vouchers = []
    for i in range(deal_buy.Amount):
        vouchers.append(Voucher.objects.create(
            DealBuy=deal_buy,
            code="%s-%s-%s" % (deal_buy.pk, i, deal_buy.Deal.pk),  # todo: check
        ))
    r = VoucherReport(queryset=vouchers)
    r.title = '[%s] deal vouchers' % deal_buy.Deal.item.name
    buffer = StringIO.StringIO()
    r.generate_by(PDFGenerator, filename=buffer)
    buffer.seek(0)
    return buffer.getvalue()


def GenerateBuyersDocument(deal):
    buyers_report = BuyersReport(queryset=Voucher.objects.filter(DealBuy__Deal=deal).order_by('DealBuy__DateBought'))
    buyers_report.title = "[%s] deal vouchers" % deal.item.name
    buffer = StringIO.StringIO()
    buyers_report.generate_by(PDFGenerator, filename=buffer)
    buffer.seek(0)
    return buffer.getvalue()


def CloseDeal(deal):
    deal.IsClosed = True
    deal.save()
    amounts = deal.BuyersCount()
    buys = deal.Buys.all()
    if deal.MinBuyers <= amounts and (not deal.MaxBuyers or amounts <= deal.MaxBuyers):
        for buy in buys:
            voucher_document = GenerateVoucherDocument(buy)
            f = open('c:\\b-%d.pdf' % buy.pk, 'wb')
            f.write(voucher_document)
            f.close()
            shoutit.controllers.email_controller.SendUserDealVoucher(buy, voucher_document)

        document = GenerateBuyersDocument(deal)
        f = open('c:\\a.pdf', 'wb')
        f.write(document)
        f.close()
        shoutit.controllers.email_controller.SendBusinessBuyersDocument(deal, document)
    else:
        for buy in buys:
            shoutit.controllers.email_controller.SendUserDealCancel(buy.user, deal)
            shoutit.controllers.payment_controller.RefundTransaction(buy.Payment.Transaction)
        shoutit.controllers.email_controller.SendBusinessDealCancel(deal)


def GetDealsToBeClosed():
    now = datetime.now()
    deals = Deal.objects.filter(expiry_date__lte=now, is_disabled=False, muted=False, IsClosed=False)
    return deals


def BuyDeal(user, deal, amount):
    deal_buy = DealBuy.objects.create(user=user, Deal=deal, Amount=amount)
    if deal.MaxBuyers and deal.BuyersCount() == deal.MaxBuyers:
        CloseDeal(deal)
    event_controller.register_event(user, EVENT_TYPE_BUY_DEAL, deal)
    return deal_buy


def GetValidVoucher(code):
    vouchers = Voucher.objects.filter(code=code, IsValidated=False).select_related('DealBuy', 'DealBuy__Deal', 'DealBuy__Deal__item',
                                                                                   'DealBuy__Deal__user',
                                                                                   'DealBuy__Deal__user__profile')
    if vouchers and len(vouchers) == 1:
        return vouchers[0]
    else:
        raise ObjectDoesNotExist


def InvalidateVoucher(voucher=None, code=''):
    if code and not voucher:
        voucher = GetValidVoucher(code)
    if voucher:
        voucher.IsValidated = True
        voucher.save()
        return voucher
    raise ObjectDoesNotExist


def GetDeal(deal_id):
    deals = Deal.objects.filter(pk=deal_id).select_related('shout', 'post', 'user', 'user__profile', 'item', 'item__currency')
    if deals:
        return deals[0]
    raise ObjectDoesNotExist


def GetOpenDeals(user=None, business=None, start_index=None, end_index=None, country='', city=''):
    now = datetime.now()
    qs = Deal.objects.filter(expiry_date__gt=now, is_disabled=False, muted=False, IsClosed=False).select_related('shout', 'post',
                                                                                                                 'user',
                                                                                                                 'user__profile',
                                                                                                                 'item', 'item__currency')
    if country:
        qs = qs.filter(country=country)
    if city:
        qs = qs.filter(city=city)
    if business:
        qs = qs.filter(user=business.user)
    qs = qs.extra(select={
        'buys_count': 'SELECT SUM("%(table)s"."%(amount)s") FROM "%(table)s" WHERE "%(table)s"."%(deal_id)s" = "%(deal_table)s"."%(deal_table_pk)s"' % {
        'table': DealBuy._meta.db_table, 'amount': DealBuy._meta.get_field_by_name('Amount')[0].column,
        'deal_id': DealBuy.Deal.field.column, 'deal_table': Deal._meta.db_table,
        'deal_table_pk': Deal._meta.get_ancestor_link(Shout).column},
    })
    if user:
        qs = qs.extra(select={
        'user_bought_deal': 'SELECT SUM("%(table)s"."%(amount)s") FROM "%(table)s" WHERE "%(table)s"."%(user_id)s" = %(uid)d AND "%(table)s"."%(deal_id)s" = "%(deal_table)s"."%(deal_table_pk)s"' % {
        'table': DealBuy._meta.db_table, 'amount': DealBuy._meta.get_field_by_name('Amount')[0].column,
        'user_id': DealBuy.user.field.column, 'deal_id': DealBuy.Deal.field.column, 'uid': user.pk, 'deal_table': Deal._meta.db_table,
        'deal_table_pk': Deal._meta.get_ancestor_link(Shout).column}})
    qs = qs.order_by('-date_published')
    qs = qs[start_index:end_index]
    return qs


def HasUserBoughtDeal(user, deal):
    return len(DealBuy.objects.filter(user=user, Deal=deal)) > 0


import shoutit.controllers.tag_controller
import shoutit.controllers.email_controller, shoutit.controllers.event_controller, shoutit.controllers.item_controller
import shoutit.controllers.payment_controller
from shoutit.models import Deal
from common.constants import POST_TYPE_DEAL, EVENT_TYPE_POST_DEAL, EVENT_TYPE_BUY_DEAL