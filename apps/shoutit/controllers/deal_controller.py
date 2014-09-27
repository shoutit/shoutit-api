import StringIO
import cgi
from datetime import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.template.context import Context
from django.template.loader import get_template
#from xhtml2pdf import pisa
from apps.shoutit import utils
import apps.shoutit.controllers.shout_controller as shout_controller
from apps.shoutit.models import DealBuy, Payment, Transaction, Voucher, Shout
from apps.shoutit.utils import GeneratePassword, asynchronous_task
from geraldo import Report, ReportBand, DetailBand, SystemField, Label, ObjectValue, Image, Rect
from reportlab.lib.colors import orange
from geraldo.utils import cm, BAND_WIDTH, TA_CENTER, TA_RIGHT
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from geraldo.generators import PDFGenerator
from apps.shoutit.templatetags.template_filters import price
import reportlab.graphics.barcode
import urllib2


def ShoutDeal(name, description, price, images, currency, tags, expiry_date, min_buyers, max_buyers, original_price, business_profile, country_code, province_code, valid_from = None, valid_to = None):
    #currency = Currency.objects.get(Code__iexact = currency)
    item = item_controller.create_item(name=name, price=price, currency=currency, images=images)

    deal = Deal(
        MinBuyers = min_buyers,
        MaxBuyers = max_buyers,
        OriginalPrice = original_price,
        Item = item,
        CountryCode = country_code,
        ProvinceCode = province_code
    )
    deal.Text = description
    deal.Type = POST_TYPE_DEAL
    deal.OwnerUser = business_profile.User
    deal.ExpiryDate = expiry_date
    deal.ValidFrom = valid_from
    deal.ValidTo = valid_to
    deal.save()

    stream = business_profile.Stream
    stream.PublishShout(deal)
    for tag in apps.shoutit.controllers.tag_controller.GetOrCreateTags(None, tags, deal.OwnerUser):
        deal.Tags.add(tag)
        tag.Stream.PublishShout(deal)

    event_controller.RegisterEvent(business_profile.User, EVENT_TYPE_POST_DEAL, deal)
    return deal


def GetConcurrentDeals(business_profile):
    return Deal.objects.GetValidDeals().filter(OwnerUser = business_profile.User, IsClosed = False)


def get_image_for_voucher(voucher_band):
    import Image
    image_url = voucher_band.instance.DealBuy.Deal.Item.GetFirstImage()
    if image_url:
        img_file = urllib2.urlopen(image_url)
        return Image.open(StringIO.StringIO(img_file.read()))
    return None


def get_qr_for_voucher(voucher_band):
    from PyQRNative import QRCode
    from PyQRNative import QRErrorCorrectLevel
    qr = QRCode(3, QRErrorCorrectLevel.L)
    qr.addData(voucher_band.instance.Code)
    qr.make()
    return qr.makeImage()


def get_barcode_for_voucher(voucher_band):
    import Image
    buffer = StringIO.StringIO()
    buffer.write(reportlab.graphics.barcode.createBarcodeImageInMemory('Code128', value = voucher_band.instance.Code, format = 'png', height = 6 * cm, width = 24 * cm))
    buffer.seek(0)
    return Image.open(buffer)


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
            SystemField(expression = '%(report_title)s', top = 0 * cm, left = 0, width = BAND_WIDTH, style = {'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
            SystemField(expression = u'Page %(page_number)d of %(page_count)d', top = 0 * cm, width = BAND_WIDTH, style = {'alignment' : TA_RIGHT}),
        ]
        borders = {'bottom' : True}

    class band_detail(ReportBand):
        height = 25.1 * cm
        elements = [
            Rect (left = 00.00 * cm, top = 00.25 * cm, width = 06.0 * cm, height = 02.50 * cm, fill = True, stroke = False, fill_color = orange), #Logo
            Label(get_value = lambda widget, band: widget.instance.DealBuy.Deal.Item.Name, style = {'wordWrap' : True, 'alignment' : TA_JUSTIFY, 'fontName': 'Helvetica-Bold', 'fontSize': 28},
                  left = 00.00 * cm, top = 03.40 * cm, width = 12.0 * cm, height = 02.50 * cm                                                  ), #Deal Name
            Label(get_value = get_validity_for_deal, style = {'wordWrap' : True, 'alignment' : TA_JUSTIFY, 'fontName': 'Helvetica-Bold', 'fontSize': 10},
                  left = 00.00 * cm, top = 06.10 * cm, width = 12.0 * cm, height = 01.00 * cm                                                  ), #Validity
            Image(left = 00.33 * cm, top = 07.60 * cm, width = 06.0 * cm, height = 06.00 * cm, get_image = get_image_for_voucher               ), #Image
            Rect (left = 00.00 * cm, top = 20.00 * cm, width = 18.5 * cm, height = 05.00 * cm, fill = True, stroke = False, fill_color = orange), #How To Use

            Image(left = 14.55 * cm, top = 00.50 * cm, width = 06.0 * cm, height = 06.00 * cm, get_image = get_qr_for_voucher                  ), #QR
            Image(left = 12.50 * cm, top = 03.70 * cm, width = 13.0 * cm, height = 02.50 * cm, get_image = get_barcode_for_voucher             ), #Barcode
            Label(get_value = lambda widget, band: widget.instance.Code, style = {'wordWrap' : True, 'alignment' : TA_CENTER, 'fontName': 'Helvetica-Bold', 'fontSize': 18},
                  left = 13.00 * cm, top = 05.20 * cm, width = 06.5 * cm, height = 00.70 * cm                                                  ), #Code
            Label(get_value = lambda widget, band: price(widget.instance.DealBuy.Deal.Item.Price, widget.instance.DealBuy.Deal.Item.Currency.Code),
                  style = {'wordWrap' : True, 'alignment' : TA_CENTER, 'fontName': 'Helvetica-Bold', 'fontSize': 24},
                  left = 13.20 * cm, top = 06.20 * cm, width = 05.5 * cm, height = 02.50 * cm, fill = True, stroke = False, fill_color = orange), #Worth
            Label(get_value = lambda widget, band: widget.instance.DealBuy.Deal.Text, style = {'wordWrap' : True, 'alignment' : TA_JUSTIFY, 'fontName': 'Helvetica', 'fontSize': 14},
                  left = 06.95 * cm, top = 09.00 * cm, width = 11.5 * cm, height = 10.50 * cm                                                  ), #Description
        ]

    class band_page_footer(ReportBand):
        height = 0.5 * cm
        elements = [
            Label(text='Shoutit Deals', top = 0.1 * cm),
            SystemField(expression = 'Printed in %(now:%Y, %b %d)s at %(now:%H:%M)s', top = 0.1 * cm, width = BAND_WIDTH, style = {'alignment' : TA_RIGHT}),
        ]
        borders = {'top' : True}


class BuyersReport(Report):
    class band_detail(DetailBand):
        height = 2.4 * cm
        elements = [
            Label(left = 0.5 * cm, get_value = get_id_for_voucher, top = 1 * cm),
            ObjectValue(expression = 'Code', left = 2.5 * cm, top = 1 * cm),
            Image(left = 8 * cm, top = 0.1 * cm, width = 4 * cm, height = 4 * cm, get_image = get_qr_for_voucher),
            Image(left = 10.5 * cm, top = 0.5 * cm, width = 16 * cm, height = 2 * cm, get_image = get_barcode_for_voucher),
        ]
        borders = {'bottom' : True}

    class band_page_header(ReportBand):
        height = 1.3 * cm
        elements = [
            SystemField(expression = '%(report_title)s', top = 0.1 * cm, left = 0, width = BAND_WIDTH, style = {'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
            SystemField(expression = u'Page %(page_number)d of %(page_count)d', top = 0.1 * cm, width = BAND_WIDTH, style = {'alignment' : TA_RIGHT}),
            Label(text = "ID", top = 0.8 * cm, left = 0.5 * cm),
            Label(text = "Code", top = 0.8 * cm, left = 2.5 * cm),
            Label(text = "QR Code", top = 0.8 * cm, left = 8 * cm),
            Label(text = "Barcode", top = 0.8 * cm, left = 12.5 * cm),
        ]
        borders = {'bottom' : True}


    class band_page_footer(ReportBand):
        height = 0.5 * cm
        elements = [
            Label(text='Shoutit Deals', top = 0.1 * cm),
            SystemField(expression = 'Printed in %(now:%Y, %b %d)s at %(now:%H:%M)s', top = 0.1 * cm, width = BAND_WIDTH, style = {'alignment' : TA_RIGHT}),
        ]
        borders = {'top' : True}

    class band_summary(ReportBand):
        height = 0.5 * cm
        elements = [
            Label(text='Total Vouchers:'),
            ObjectValue(expression = 'count(Code)', left = 5 * cm),
        ]
        borders = {'top' : True}


def GenerateVoucherDocument(deal_buy):
    vouchers = []
    for i in range(deal_buy.Amount):
        vouchers.append(Voucher.objects.create(
            DealBuy = deal_buy,
            Code = utils.IntToBase62(deal_buy.pk) + utils.RandomBase62(4) + utils.IntToBase62(i) + utils.RandomBase62(2) + utils.IntToBase62(deal_buy.Deal.pk),
        ))
    r = VoucherReport(queryset = vouchers)
    r.title =  '[%s] deal vouchers' % deal_buy.Deal.Item.Name
    buffer = StringIO.StringIO()
    r.generate_by(PDFGenerator, filename = buffer)
    buffer.seek(0)
    return buffer.getvalue()


def GenerateBuyersDocument(deal):
    buyers_report = BuyersReport(queryset = Voucher.objects.filter(DealBuy__Deal = deal).order_by('DealBuy__DateBought'))
    buyers_report.title = "[%s] deal vouchers" % deal.Item.Name
    buffer = StringIO.StringIO()
    buyers_report.generate_by(PDFGenerator, filename = buffer)
    buffer.seek(0)
    return buffer.getvalue()


@asynchronous_task()
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
            apps.shoutit.controllers.email_controller.SendUserDealVoucher(buy, voucher_document)

        document = GenerateBuyersDocument(deal)
        f = open('c:\\a.pdf', 'wb')
        f.write(document)
        f.close()
        apps.shoutit.controllers.email_controller.SendBusinessBuyersDocument(deal, document)
    else:
        for buy in buys:
            apps.shoutit.controllers.email_controller.SendUserDealCancel(buy.User, deal)
            apps.shoutit.controllers.payment_controller.RefundTransaction(buy.Payment.Transaction)
        apps.shoutit.controllers.email_controller.SendBusinessDealCancel(deal)


def GetDealsToBeClosed():
    now = datetime.now()
    deals = Deal.objects.filter(ExpiryDate__lte = now, IsDisabled = False, IsMuted = False, IsClosed = False)
    return deals


def BuyDeal(user, deal, amount):
    deal_buy = DealBuy.objects.create(User = user, Deal = deal, Amount = amount)
    if deal.MaxBuyers and deal.BuyersCount() == deal.MaxBuyers:
        CloseDeal(deal)
    event_controller.RegisterEvent(user, EVENT_TYPE_BUY_DEAL, deal)
    return deal_buy


def GetValidVoucher(code):
    vouchers = Voucher.objects.filter(Code = code, IsValidated = False).select_related('DealBuy', 'DealBuy__Deal', 'DealBuy__Deal__Item', 'DealBuy__Deal__OwnerUser', 'DealBuy__Deal__OwnerUser__Profile')
    if vouchers and len(vouchers) == 1:
        return vouchers[0]
    else:
        raise ObjectDoesNotExist


def InvalidateVoucher(voucher = None, code = ''):
    if code and not voucher:
        voucher = GetValidVoucher(code)
    if voucher:
        voucher.IsValidated = True
        voucher.save()
        return voucher
    raise ObjectDoesNotExist


def GetDeal(deal_id):
    deals = Deal.objects.filter(pk = deal_id).select_related('shout', 'post', 'OwnerUser', 'OwnerUser__Profile', 'Item', 'Item__Currency')
    if deals:
        return deals[0]
    raise ObjectDoesNotExist


def GetOpenDeals(user = None, business = None, start_index = None, end_index = None, country_code = '', province_code = ''):
    now = datetime.now()
    qs = Deal.objects.filter(ExpiryDate__gt = now, IsDisabled = False, IsMuted = False, IsClosed = False).select_related('shout', 'post', 'OwnerUser', 'OwnerUser__Profile', 'Item', 'Item__Currency')
    if country_code:
        qs = qs.filter(CountryCode = country_code)
    if province_code:
        qs = qs.filter(ProvinceCode = province_code)
    if business:
        qs = qs.filter(OwnerUser = business.User)
    qs = qs.extra(select = {
        'buys_count' : 'SELECT SUM("%(table)s"."%(amount)s") FROM "%(table)s" WHERE "%(table)s"."%(deal_id)s" = "%(deal_table)s"."%(deal_table_pk)s"' % {'table' : DealBuy._meta.db_table, 'amount' : DealBuy._meta.get_field_by_name('Amount')[0].column, 'deal_id' : DealBuy.Deal.field.column, 'deal_table' : Deal._meta.db_table, 'deal_table_pk' : Deal._meta.get_ancestor_link(Shout).column},
    })
    if user:
        qs = qs.extra(select = {'user_bought_deal' : 'SELECT SUM("%(table)s"."%(amount)s") FROM "%(table)s" WHERE "%(table)s"."%(user_id)s" = %(uid)d AND "%(table)s"."%(deal_id)s" = "%(deal_table)s"."%(deal_table_pk)s"' % {'table' : DealBuy._meta.db_table, 'amount' : DealBuy._meta.get_field_by_name('Amount')[0].column, 'user_id' : DealBuy.User.field.column, 'deal_id' : DealBuy.Deal.field.column, 'uid' : user.pk, 'deal_table' : Deal._meta.db_table, 'deal_table_pk' : Deal._meta.get_ancestor_link(Shout).column}})
    qs = qs.order_by('-DatePublished')
    qs = qs[start_index:end_index]
    return qs


def HasUserBoughtDeal(user, deal):
    return len(DealBuy.objects.filter(User = user, Deal = deal)) > 0

import apps.shoutit.controllers.shout_controller
import apps.shoutit.controllers.tag_controller
import apps.shoutit.controllers.email_controller,event_controller,item_controller
import apps.shoutit.controllers.payment_controller
import apps.shoutit.controllers.shout_controller
from apps.shoutit.models import StoredImage, Deal, Currency, Item, Post
from apps.shoutit.constants import POST_TYPE_DEAL,EVENT_TYPE_POST_DEAL,EVENT_TYPE_BUY_DEAL