import datetime
import pika
from apps.shoutit.utils import asynchronous_task
import apps.shoutit.settings as settings
import os
from apns import Payload, APNs

PROJECT_PATH = os.path.abspath(os.path.dirname(__name__))
apns_instance = APNs(use_sandbox=False, cert_file=PROJECT_PATH+'/ShoutWebsite/static/Certificates/iphone/ShoutitPushCer.pem', key_file=PROJECT_PATH+'/ShoutWebsite/static/Certificates/iphone/ShoutitKey.pem')

import json
import socket

from django.utils.translation import ugettext as _


GET_USER_CONNECTED_CLIENTS_COUNT = 1

try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(settings.RABBIT_MQ_HOST, settings.RABBIT_MQ_PORT))
except:
    connection = None


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
    try:
        from common.tagged_cache import TaggedCache
        apns_tokens = TaggedCache.get('apns|%s' % username)
        apns_count = 0
        if apns_tokens:
            for token in apns_tokens:
                message = notification.FromUser.username + " has"
                userProfile = apps.shoutit.controllers.user_controller.GetUser(username)
                unread_conversations_num = apps.shoutit.controllers.message_controller.UnReadConversationsCount(userProfile.User)
                notifications_count = apps.shoutit.controllers.notifications_controller.GetUserNotificationsWithoutMessagesCount(userProfile.User)
                customMessage = {}
                if notification.Type == NOTIFICATION_TYPE_FOLLOWSHIP:
                    message += " " + _("started listening to your shouts")
                    customMessage = {'URCnv':unread_conversations_num}
                elif notification.Type == NOTIFICATION_TYPE_MESSAGE:
                    message += " " + _("sent you a message")
                    customMessage = {'UC': unread_conversations_num, 'CID': utils.IntToBase62(notification.AttachedObject.Conversation_id)}
                payload = Payload(alert=message, sound="default", badge=notifications_count, custom=customMessage)
                try:
                    apns_instance.gateway_server.send_notification(token, payload)
                except:
                    apns_instance = APNs(use_sandbox=False, cert_file=PROJECT_PATH + '/ShoutWebsite/static/Certificates/iphone/ShoutitPushCer.pem', key_file=PROJECT_PATH+'/ShoutWebsite/static/Certificates/iphone/ShoutitKey.pem')
                    apns_instance.gateway_server.send_notification(token, payload)

            if count and count == len(apns_tokens):
                return
        try:
            channel = connection.channel()
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
        channel = connection.channel()
        channel.queue_declare(queue=str('Shout_%s' % username), durable=True)
        channel.basic_publish(exchange='', routing_key=str('Shout_%s' % username), body=message, properties=pika.BasicProperties(content_type="text/plain", delivery_mode=2))
    except Exception, e:
        print e.message


@asynchronous_task()
def BroadcastRealtimeMessage(message, city='', username='', post=None):
    try:
        channel = connection.channel()
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
        channel = connection.channel()
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
        channel = connection.channel()
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
        channel = connection.channel()
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
        channel = connection.channel()
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
        channel = connection.channel()
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
        channel = connection.channel()
        exchange = str('Shout_E_post_%s' % post.pk)
        queue = str('Shout_%s' % username)
        channel.queue_declare(queue=queue, durable=True)
        channel.exchange_declare(exchange=exchange, type='fanout')
        channel.queue_unbind(exchange=exchange, queue=queue)
    except Exception, e:
        print e.message

from apps.shoutit import utils
from apps.shoutit.constants import NOTIFICATION_TYPE_FOLLOWSHIP, NOTIFICATION_TYPE_MESSAGE
import apps.shoutit.controllers.message_controller
import apps.shoutit.controllers.notifications_controller
import apps.shoutit.controllers.user_controller
from apps.shoutit.api.renderers import render_notification