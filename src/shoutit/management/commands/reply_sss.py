# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from shoutit.controllers import message_controller
from shoutit.models import Conversation, DBCLConversation
import random


class Command(BaseCommand):
    help = 'Reply on behalf of SSS users.'
    arabic_replies = ["العفو تم البيع", "شكرا، بس للاسف تم البيع"]
    english_replies = ["sorry sold", "it is sold already sorry", "thanks for your message but it has been already sold", "sold"]

    def handle(self, *args, **options):
        # get conversations
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today + datetime.timedelta(days=-1)
        two_days_ago = today + datetime.timedelta(days=-2)
        conversations = Conversation.objects.filter(created_at__gte=two_days_ago,
                                                    created_at__lt=yesterday,
                                                    shout__is_sss=True)
        for conversation in conversations:
            shout = conversation.attached_object
            sss_user = shout.user
            if conversation.messages.filter(user=sss_user).exists():
                # sss user already replied
                continue
            # set the text
            text = random.choice(self.english_replies)
            # send the message
            message_controller.send_message(conversation=conversation, user=sss_user, text=text)
            # disable the shout
            shout.is_disabled = True
            shout.save()
            # delete dbcl conversations
            DBCLConversation.objects.filter(to_user=sss_user).delete()

        self.stdout.write("Successfully replied on behalf of sss users")
