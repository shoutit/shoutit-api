import datetime
import json
import socket

import pika
from django.conf import settings
from django.utils.translation import ugettext as _

from common.constants import NOTIFICATION_TYPE_LISTEN, NOTIFICATION_TYPE_MESSAGE
from apps.shoutit.utils import asynchronous_task
from apps.shoutit.api.renderers import render_notification


GET_USER_CONNECTED_CLIENTS_COUNT = 1

try:
    if settings.REALTIME_SERVER_ON:
        realtime_connection = pika.BlockingConnection(pika.ConnectionParameters(settings.RABBIT_MQ_HOST, settings.RABBIT_MQ_PORT))
except Exception, e:
    print e.message
    realtime_connection = None


def GetUserConnectedClientsCount(username):
    try:
        from common.tagged_cache import TaggedCache
        apns_tokens = TaggedCache.get('apns|%s' % username)
        count = 0
        if apns_tokens:
            count += len(apns_tokens)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((settings.REALTIME_SERVER_ADDRESS, settings.REALTIME_SERVER_API_PORT))
        s.send('{"method" : %d, "username" : "%s"}' % (GET_USER_CONNECTED_CLIENTS_COUNT, username))
        result = s.recv(4096)
        s.close()
        obj = json.loads(result, 'utf-8')
        if obj.has_key('error'):
            return 0 + count
        else:
            return obj['result'] + count
    except:
        return 0 + count


@asynchronous_task()
def SendNotification(notification, username, count=0):
    from apps.shoutit.controllers.user_controller import get_profile
    from apps.shoutit.controllers.message_controller import UnReadConversationsCount
    from apps.shoutit.controllers.notifications_controller import GetUserNotificationsWithoutMessagesCount
    try:
        from common.tagged_cache import TaggedCache
        apns_tokens = TaggedCache.get('apns|%s' % username)
        apns_count = 0
        if apns_tokens:
            for token in apns_tokens:
                message = notification.FromUser.username + " has"
                userProfile = get_profile(username)
                unread_conversations_num = UnReadConversationsCount(userProfile.user)
                notifications_count = GetUserNotificationsWithoutMessagesCount(userProfile.user)
                customMessage = {}
                if notification.Type == NOTIFICATION_TYPE_LISTEN:
                    message += " " + _("started listening to your shouts")
                    customMessage = {'URCnv':unread_conversations_num}
                elif notification.Type == NOTIFICATION_TYPE_MESSAGE:
                    message += " " + _("sent you a message")
                    customMessage = {'UC': unread_conversations_num, 'CID': notification.attached_object.Conversation_id}

            if count and count == len(apns_tokens):
                return
        try:
            channel = realtime_connection.channel()
            channel.queue_declare(queue=str('Shout_' + username), durable=True)
            message = json.dumps(render_notification(notification))
            channel.basic_publish(exchange='', routing_key=str('Shout_%s' % username), body=message, properties=pika.BasicProperties(content_type="text/plain", delivery_mode=2))
        except Exception, e:
            print e.message
    except Exception, e:
        print e.message


def WrapRealtimeMessage(message, type):
    result = {
        'message': message,
        'type': type,
        'date_sent': datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S%z')
    }
    return json.dumps(result)


@asynchronous_task()
def SendRealtimeMessage(message, username):
    try:
        channel = realtime_connection.channel()
        channel.queue_declare(queue=str('Shout_%s' % username), durable=True)
        channel.basic_publish(exchange='', routing_key=str('Shout_%s' % username), body=message, properties=pika.BasicProperties(content_type="text/plain", delivery_mode=2))
    except Exception, e:
        print e.message


@asynchronous_task()
def BroadcastRealtimeMessage(message, city='', username='', post=None):
    try:
        channel = realtime_connection.channel()
        if city:
            exchange = str('Shout_E_%s_%s' % ('city', city))
            channel.exchange_declare(exchange=exchange, type='fanout')
            channel.basic_publish(exchange=exchange, routing_key='', body=message, properties=pika.BasicProperties(content_type="text/plain", delivery_mode=2))
        if username:
            exchange = str('Shout_E_%s_%s' % ('user', username))
            channel.exchange_declare(exchange=exchange, type='fanout')
            channel.basic_publish(exchange=exchange, routing_key='', body=message, properties=pika.BasicProperties(content_type="text/plain", delivery_mode=2))
        if post:
            exchange = str('Shout_E_%s_%s' % ('post', str(post.pk)))
            channel.exchange_declare(exchange=exchange, type='fanout')
            channel.basic_publish(exchange=exchange, routing_key='', body=message, properties=pika.BasicProperties(content_type="text/plain", delivery_mode=2))
    except Exception, e:
        print e.message


@asynchronous_task()
def BindUserToCity(username, city):
    try:
        channel = realtime_connection.channel()
        exchange = str('Shout_E_city_%s' % city)
        queue = str('Shout_%s' % username)
        channel.queue_declare(queue=queue, durable=True)
        channel.exchange_declare(exchange=exchange, type='fanout')
        channel.queue_bind(exchange=exchange, queue=queue)
    except Exception, e:
        print e.message


@asynchronous_task()
def BindUserToUser(username, username_to):
    try:
        channel = realtime_connection.channel()
        exchange = str('Shout_E_user_%s' % username_to)
        queue = str('Shout_%s' % username)
        channel.queue_declare(queue=str(queue), durable=True)
        channel.exchange_declare(exchange=exchange, type='fanout')
        channel.queue_bind(exchange=exchange, queue=queue)
    except Exception, e:
        print e.message


@asynchronous_task()
def BindUserToPost(username, post):
    try:
        channel = realtime_connection.channel()
        exchange = str('Shout_E_post_%s' % post.pk)
        queue = str('Shout_%s' % username)
        channel.queue_declare(queue=queue, durable=True)
        channel.exchange_declare(exchange=exchange, type='fanout')
        channel.queue_bind(exchange=exchange, queue=queue)
    except Exception, e:
        print e.message


@asynchronous_task()
def UnbindUserFromCity(username, city):
    try:
        channel = realtime_connection.channel()
        exchange = str('Shout_E_city_%s' % city)
        queue = str('Shout_%s' % username)
        channel.queue_declare(queue=queue, durable=True)
        channel.exchange_declare(exchange=exchange, type='fanout')
        channel.queue_unbind(exchange=exchange, queue=queue)
    except Exception, e:
        print e.message


@asynchronous_task()
def UnbindUserFromUser(username, username_from):
    try:
        channel = realtime_connection.channel()
        exchange = str('Shout_E_user_%s' % username_from)
        queue = str('Shout_%s' % username)
        channel.queue_declare(queue=queue, durable=True)
        channel.exchange_declare(exchange=exchange, type='fanout')
        channel.queue_unbind(exchange=exchange, queue=queue)
    except Exception, e:
        print e.message


@asynchronous_task()
def UnbindUserFromPost(username, post):
    try:
        channel = realtime_connection.channel()
        exchange = str('Shout_E_post_%s' % post.pk)
        queue = str('Shout_%s' % username)
        channel.queue_declare(queue=queue, durable=True)
        channel.exchange_declare(exchange=exchange, type='fanout')
        channel.queue_unbind(exchange=exchange, queue=queue)
    except Exception, e:
        print e.message
