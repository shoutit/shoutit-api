# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from shoutit.controllers import message_controller
from shoutit.controllers.notifications_controller import sms_sss_user
from shoutit.models import Conversation, DBCLConversation
import random

arabic_replies = ["العفو تم البيع", "شكرا، بس للاسف تم البيع", "عفوا تم البيع", "مباع", "غير موجود حاليا", "غير موجود", "عفوا انباع", "للاسف انباعت", "شكرا بس تم البيع", ""]
english_replies = ["sorry sold", "it is sold already sorry", "been already sold", "sold", ""]


class Command(BaseCommand):
    help = 'Reply on behalf of SSS users.'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('--days', default=2, type=int)

    def handle(self, *args, **options):
        # get conversations
        now = timezone.now()
        four_hours_ago = now + datetime.timedelta(hours=-0)
        days_ago = now + datetime.timedelta(days=-options['days'])
        conversations = Conversation.objects.filter(created_at__gte=days_ago,
                                                    created_at__lt=four_hours_ago,
                                                    shout__is_sss=True)
        replies_count = 0
        for conversation in conversations:
            shout = conversation.about
            sss_user = shout.user
            if conversation.messages.filter(user=sss_user).exists():
                # sss user already replied
                continue
            reply_sss(conversation, shout, sss_user)
            replies_count += 1
        self.stdout.write("Successfully replied on behalf of %s sss users" % replies_count)


def reply_sss(conversation, shout, sss_user):
    # set the text
    sss_profile = sss_user.profile
    mobile = sss_profile.mobile
    if mobile:
        text = mobile
        last_message = conversation.last_message
        # send the message
        message_controller.send_message(conversation=conversation, user=sss_user, text=text)
        # sms the sss_user again
        sms_sss_user(sss_user, from_user=last_message.user, message=last_message, sms_anyway=True)
    else:
        if sss_user.profile.country in ['JO', 'EG', 'SA', 'OM', 'BH']:
            text = random.choice(arabic_replies)
        else:  # ['AE', 'QA', 'KQ', 'BH', ...]
            text = random.choice(english_replies)
        # send the message
        message_controller.send_message(conversation=conversation, user=sss_user, text=text)
        # leave conversation
        conversation.mark_as_deleted(sss_user)
        # disable the shout
        shout.is_disabled = True
        shout.save()
        # delete dbcl conversations
        DBCLConversation.objects.filter(to_user=sss_user).delete()
