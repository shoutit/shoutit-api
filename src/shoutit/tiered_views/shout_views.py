import json

import re
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt

from shoutit.models import DBCLConversation, CLUser, DBUser, Category
from shoutit.controllers.message_controller import send_message
from shoutit.controllers.user_controller import sign_up_sss4
from shoutit.controllers import shout_controller
from shoutit.permissions import INITIAL_USER_PERMISSIONS
from shoutit.utils import JsonResponse, JsonResponseBadRequest

import logging

logger = logging.getLogger('shoutit.error')


@csrf_exempt
def inbound_email(request):
    data = request.POST or request.GET or {}
    if request.method == 'GET':
        print data
        return JsonResponse(data)
    elif request.method == 'POST':
        msg = json.loads(data['mandrill_events'])[0]['msg']
        in_email = msg['email']
        text = msg['text']

        try:
            ref = re.search("\{ref:(.+)\}", text).groups()[0]
        except AttributeError:
            return JsonResponse({
                'error': "ref wasn't passed in the reply, we can't process the message any further."})

        try:
            text = '\n'.join(text.split('\n> ')[0].splitlines()[:-2])
        except AttributeError:
            return JsonResponse({'error': "we couldn't process the message text."})

        try:
            dbcl_conversation = DBCLConversation.objects.get(ref=ref)
        except DBCLConversation.DoesNotExist, e:
            print e
            return JsonResponse({'error': str(e)})

        from_user = dbcl_conversation.to_user
        to_user = dbcl_conversation.from_user
        shout = dbcl_conversation.shout

        message = send_message(conversation=None, user=from_user, to_users=[from_user, to_user],
                               about=shout, text=text)
        return JsonResponse({'success': True, 'message_id': message.pk})


@csrf_exempt
def shout_sss4(request):
    data = request.json_data
    shout = data['shout']
    # check of previous ad
    try:
        if shout['source'] == 'cl':
            CLUser.objects.get(cl_email=shout['cl_email'])
        elif shout['source'] == 'db':
            DBUser.objects.get(db_link=shout['link'])
        else:
            msg = "Unknown ad source: " + shout['source']
            logger.warn(msg)
            return JsonResponseBadRequest({'error': msg})
        msg = "Ad already exits. " + shout['link']
        logger.warn(msg)
        return JsonResponseBadRequest({'error': msg})
    except ObjectDoesNotExist:
        pass

    # user creation
    try:
        if shout['source'] == 'cl':
            user = sign_up_sss4(email=shout['cl_email'], lat=shout['lat'], lng=shout['lng'],
                                city=shout['city'], country=shout['country'], dbcl_type='cl')
        elif shout['source'] == 'db':
            user = sign_up_sss4(None, lat=shout['lat'], lng=shout['lng'], city=shout['city'],
                                country=shout['country'], dbcl_type='db', db_link=shout['link'])
        else:
            raise Exception('Unknown ad source')
    except Exception, e:
        msg = "User Creation Error: " + str(e)
        logger.error(msg)
        return JsonResponseBadRequest({'error': msg})

    # shout creation
    tags = shout['tags']
    if isinstance(tags, basestring):
        tags = tags.split(' ')

    if not tags:
        msg = "Invalid tags: " + shout['tags']
        logger.error(msg)
        return JsonResponseBadRequest({'error': msg})

    category = shout.get('category')
    try:
        category = Category.objects.get(name=category)
    except Category.DoesNotExist:
        return JsonResponseBadRequest({'error': "Category %s does not exist." % category})

    try:
        if shout['type'] == 'request':
            shout = shout_controller.post_request(
                name=shout['title'], text=shout['description'], price=float(shout['price']),
                currency=shout['currency'],
                latitude=float(shout['lat']), longitude=float(shout['lng']),
                country=shout['country'], city=shout['city'],
                tags=tags, images=shout['images'], shouter=user, is_sss=True,
                exp_days=settings.MAX_EXPIRY_DAYS_SSS, category=category
            )
        elif shout['type'] == 'offer':
            shout = shout_controller.post_offer(
                name=shout['title'], text=shout['description'], price=float(shout['price']),
                currency=shout['currency'],
                latitude=float(shout['lat']), longitude=float(shout['lng']),
                country=shout['country'], city=shout['city'],
                tags=tags, images=shout['images'], shouter=user, is_sss=True,
                exp_days=settings.MAX_EXPIRY_DAYS_SSS, category=category
            )

    except Exception, e:
        logger.error(str(e))
        return JsonResponseBadRequest({'error': "Shout Creation Error: " + str(e)})

    # good bye!
    return JsonResponse({'success': True})
