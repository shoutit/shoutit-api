# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import re

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt

from common.constants import ENUM_XHR_RESULT, DEFAULT_PAGE_SIZE
from apps.shoutit.models import User
from apps.shoutit.models import Business, Deal, ServiceBuy
from apps.shoutit.controllers import deal_controller, user_controller
from apps.shoutit.forms import DealForm
from apps.shoutit.tiered_views.renderers import get_initial_json_response, json_data_renderer, deals_stream_json
from apps.shoutit.tiered_views.validators import object_exists_validator
from apps.shoutit.xhr_utils import xhr_respond
from apps.shoutit.controllers import payment_controller
from renderers import page_html
from validators import form_validator
from apps.shoutit.tiers import non_cached_view, refresh_cache, CACHE_TAG_DEALS, CACHE_TAG_STREAMS, ResponseResult, ValidationResult, \
    RESPONSE_RESULT_ERROR_BAD_REQUEST, cached_view, CACHE_LEVEL_GLOBAL, CACHE_TAG_VOUCHERS, RESPONSE_RESULT_ERROR_FORBIDDEN
from apps.shoutit.permissions import PERMISSION_SHOUT_DEAL


def deal_to_dict(deal):
    result = {
        'name': deal.Item.Name,
        'text': deal.Text,
        'pirce': deal.Item.Price,
        'expiry_date': deal.ExpiryDate.strftime('%d/%m/%Y %H:%M:%S%z'),
        'min_buyers': deal.MinBuyers,
        'max_buyers': deal.MaxBuyers,
        'original_price': deal.OriginalPrice,
        'currency': deal.Item.Currency.Code,
        'country': deal.CountryCode,
        'city': deal.ProvinceCode,
    }
    if deal.ValidFrom:
        result['valid_from'] = deal.ValidFrom.strftime('%d/%m/%Y %H:%M:%S%z')
    if deal.ValidTo:
        result['valid_to'] = deal.ValidTo.strftime('%d/%m/%Y %H:%M:%S%z')
    if hasattr(deal, 'user_bought_deal'):
        result['user_bought_deal'] = deal.user_bought_deal or 0
    return result


def deals_renderer_json(request, result, *args, **kwargs):
    if not result.errors:
        data = {'deals': []}
        if result.data.has_key('deals'):
            for deal in result.data['deals']:
                data['deals'].append(deal_to_dict(deal))
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, result.messages and result.messages[0][1] or '', data=data, message_type='success')
    else:
        return get_initial_json_response(request, result)


def deal_renderer_json(request, result, *args, **kwargs):
    if not result.errors:
        # Tags
        # Business Profile
        data = deal_to_dict(result.data['deal'])
        for k in ['user_bought_deal', 'available_count', 'buyers_count', 'is_closed']:
            if result.data.has_key(k):
                data[k] = result.data[k]
        return xhr_respond(ENUM_XHR_RESULT.SUCCESS, result.messages and result.messages[0][1] or '', data=data, message_type='success')
    else:
        return get_initial_json_response(request, result)


CONCURRENT_DEALS_SERVICE = 'CONCURRENT_DEALS'


def shout_deal_validator(request):
    result = form_validator(request, DealForm)
    if result.valid:
        bp = Business.objects.get(user__pk=request.user.pk)
        concurrent_deals = deal_controller.GetConcurrentDeals(bp)
        if False:  # concurrent_deals:
            service_buy = ServiceBuy.objects.GetUserServiceBuyRemaining(request.user, CONCURRENT_DEALS_SERVICE)
            if not service_buy or service_buy[0]['buys_count'] - service_buy[0]['used_count'] < 1:
                return ValidationResult(False, {}, [RESPONSE_RESULT_ERROR_BAD_REQUEST],
                                        [('error', _('You can\'t have concurrent deals, you must buy that service.'))])
    return result


@non_cached_view(
    html_renderer=lambda request, result: page_html(request, result, 'shout_deal.html', _('Shout a deal')),
    json_renderer=deal_renderer_json,
    permissions_required=[PERMISSION_SHOUT_DEAL],
    login_required=True,
    validator=shout_deal_validator,
)
@refresh_cache(tags=[CACHE_TAG_DEALS, CACHE_TAG_STREAMS])
def shout_deal(request):
    result = ResponseResult()
    if request.method == 'POST':
        result.data['form'] = DealForm(request.POST, request.FILES)
        result.data['form'].is_valid()
        bp = Business.objects.get(user__pk=request.user.pk)
        images = []
        if request.POST.has_key('images[]'):
            images = request.POST.getlist('images[]')
        elif request.POST.has_key('images'):
            images = request.POST.getlist('images')
        result.data['deal'] = deal_controller.ShoutDeal(
            result.data['form'].cleaned_data['name'],
            result.data['form'].cleaned_data['description'],
            result.data['form'].cleaned_data['price'],
            images,
            result.data['form'].cleaned_data['currency'],
            result.data['form'].cleaned_data['tags'].split(' '),
            result.data['form'].cleaned_data['expiry_date'],
            result.data['form'].cleaned_data['min_buyers'],
            result.data['form'].cleaned_data['max_buyers'],
            result.data['form'].cleaned_data['original_price'],
            bp,
            result.data['form'].cleaned_data['country'],
            result.data['form'].cleaned_data['city'],
            result.data['form'].cleaned_data['valid_from'],
            result.data['form'].cleaned_data['valid_to'],
        )
        result.messages.append(('success', _('Your deal was shouted successfully')))
    else:
        result.data['form'] = DealForm(initial={'expiry_date': datetime.now() + timedelta(7)})
    return result


@cached_view(
    level=CACHE_LEVEL_GLOBAL,
    tags=[CACHE_TAG_VOUCHERS],
    json_renderer=json_data_renderer,
    html_renderer=lambda request, result: page_html(request, result, 'voucher_control.html', _('Shout a deal')),
    login_required=True,
    methods=['GET'],
)
def is_voucher_valid(request):
    result = ResponseResult()
    if request.GET.has_key('code') and request.GET['code']:
        try:
            voucher = deal_controller.GetValidVoucher(request.GET['code'])
            if voucher.DealBuy.Deal.business.user == request.user:
                result.data['is_valid'] = True
                result.data['deal'] = voucher.DealBuy.Deal.Item.Name
                return result
            else:
                result.errors.append(RESPONSE_RESULT_ERROR_FORBIDDEN)
                result.messages.append(('error', _('You don\'t own this voucher.')))
                return result
        except ObjectDoesNotExist:
            pass
    result.data['is_valid'] = False
    result.data['deal'] = ''
    return result


@non_cached_view(
    json_renderer=json_data_renderer,
    html_renderer=lambda request, result: page_html(request, result, 'voucher_control.html', _('Shout a deal')),
    methods=['GET'],
    login_required=True,
)
@refresh_cache(tags=[CACHE_TAG_VOUCHERS])
def invalidate_voucher(request):
    result = ResponseResult()
    if request.GET.has_key('code') and request.GET['code']:
        try:
            voucher = deal_controller.GetValidVoucher(request.GET['code'])
            if voucher.DealBuy.Deal.business.user == request.user:
                deal_controller.InvalidateVoucher(voucher=voucher)
                result.data['is_validated'] = True
                result.data['deal'] = voucher.DealBuy.Deal.Item.Name
                return result
            else:
                result.errors.append(RESPONSE_RESULT_ERROR_FORBIDDEN)
                result.messages.append(('error', _('You don\'t own this voucher.')))
                return result
        except ObjectDoesNotExist:
            pass
    result.data['is_validated'] = False
    result.data['deal'] = ''
    return result


@cached_view(
    tags=[CACHE_TAG_DEALS],
    methods=['GET'],
    validator=lambda request, deal_id: object_exists_validator(deal_controller.GetDeal, _('Deal does not exist.'), deal_id),
    json_renderer=deal_renderer_json,
    html_renderer=lambda request, result, deal_id: page_html(request, result, 'deal.html'),
)
def view_deal(request, deal_id):
    deal = deal_controller.GetDeal(deal_id)

    result = ResponseResult()
    result.data['deal'] = deal
    if request.user.is_authenticated():
        result.data['user_bought_deal'] = deal_controller.HasUserBoughtDeal(request.user, deal)
    result.data['buyers_count'] = deal.BuyersCount()
    if deal.MaxBuyers:
        result.data['available_count'] = deal.MaxBuyers - result.data['buyers_count']
    result.data['is_closed'] = deal.IsClosed or deal.ExpiryDate <= datetime.now()
    return result


def close_deal(request, deal_id):
    deal = Deal.objects.get(pk=deal_id)
    deal_controller.CloseDeal(deal)
    return HttpResponse('{}', content_type='application/json')


@non_cached_view(
    methods=['GET'],
    json_renderer=deals_renderer_json,
    html_renderer=lambda request, result: page_html(request, result, 'deals.html'),
)
def view_deals(request):
    result = ResponseResult()
    result.data['deals'] = deal_controller.GetOpenDeals(request.user.is_authenticated() and request.user or None,
                                                        country_code=request.session.has_key('user_country') and request.session[
                                                            'user_country'] or '',
                                                        province_code=request.session.has_key('user_city') and request.session[
                                                            'user_city'] or '')
    return result


@non_cached_view(html_renderer=lambda request, result: page_html(request, result, 'paypal.html'))
def paypal(request):
    result = ResponseResult()
    result.data['form'] = payment_controller.GetPaypalFormForDeal(Deal.objects.get(pk=17407), User.objects.get(username='mpcabd'), 3)
    result.data['sform'] = payment_controller.GetPaypalFormForSubscription(User.objects.get(username='mrabooode'))
    result.data['cpsp_dict'] = payment_controller.GetCPSPFormForDeal(Deal.objects.get(pk=17407), User.objects.get(username='mpcabd'), 3)
    return result


@non_cached_view(html_renderer=lambda request, result, *args, **kwargs: page_html(request, result, 'paypal.html'))
@csrf_exempt
def cpsp_action(request, action):
    regex = re.compile(r'(\w+)_(\w+)_U_([^_]+)(?:_x_(\d+))?')
    if request.POST.has_key('STATUS') and request.POST.has_key('orderID'):
        transaction_data = 'CPSP TXN #%s' % request.POST['PAYID']
        transaction_identifier = 'CPSP#%s' % request.POST['PAYID']
        match = regex.match(request.POST['orderID'])
        if match:
            item_type, item_id, user_id, amount = match.groups()
            if request.POST['STATUS'] in ['5', '9']:
                if item_type == 'D':
                    payment_controller.PayForDeal(user_id, item_id, amount, transaction_data, transaction_identifier)
                elif item_id == 'SERVICE':
                    payment_controller.PayForService(user_id, item_id, amount, transaction_data, transaction_identifier)
                else:
                    pass
            elif request.POST['STATUS'] in ['6', '7', '8']:
                if item_type == 'D':
                    payment_controller.CancelPaymentForDeal(user_id, item_id, transaction_data, transaction_identifier)
                elif item_id == 'SERVICE':
                    payment_controller.CancelPaymentForService(user_id, item_id, transaction_data, transaction_identifier)
                else:
                    pass
    print action, dict(request.POST), dict(request.GET)
    print '*' * 5
    result = ResponseResult()
    return result


@non_cached_view(methods=['GET'],
                 json_renderer=lambda request, result, *args: deals_stream_json(request, result))
def deals_stream(request, business_name, page_num=None):
    if not page_num:
        page_num = 1
    else:
        page_num = int(page_num)
    result = ResponseResult()
    business = user_controller.get_profile(business_name)

    start_index = DEFAULT_PAGE_SIZE * (page_num - 1)
    end_index = DEFAULT_PAGE_SIZE * page_num

    result.data['deals'] = deal_controller.GetOpenDeals(request.user.is_authenticated() and request.user or None, business, start_index,
                                                        end_index)
    return result
