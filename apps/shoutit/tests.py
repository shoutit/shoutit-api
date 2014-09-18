"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import glob
import os
from symbol import decorator
from django.test import TestCase
from apps.shoutit.constants import *
from apps.shoutit.controllers.message_controller import MessageController
import apps.shoutit.controllers.shout_controller as ShoutController
from apps.shoutit.controllers.tag_controller import TagController
from apps.shoutit.controllers.user_controller import UserController
import subprocess
import datetime

def create_users():
    UserController.SignUpUser(None, 'User_%d' % 0, 'last', '123','user_%d@hotmail.com' %0 ,u'971551987671')
    UserController.SignUpUser(None, 'User_%d' % 1, 'last', '123', 'user_%d@hotmail.com' %1 ,u'971551987673')
    UserController.SignUpUser(None, 'User_%d' % 2, 'last', '123','user_%d@hotmail.com' %2 )


class UserTestCase(TestCase):
    def setUp(self):
        create_users()

    def test_GetUser(self):
        for i in range(3):
            user = UserController.GetUserByEmail('user_%d@hotmail.com' %i)
            self.assertNotEqual(user, None, "User User_%d couldn't be Retrieved." % i)

    def test_GetUserByToken(self):
        for i in range(3):
            user = UserController.GetUserByEmail('user_%d@hotmail.com' %i)
            token = UserController.GetUserToken(user)
            user = UserController.GetUserByToken(token.Token)
            self.assertNotEqual(user, None, "User User_%d couldn't be Retrieved." % i)
            self.assertEqual(user.username, 'User_%d' % i, "Retrieved %s instaded of User_%d" %(user.username , i))

    def test_CompleteSignUp(self):
        for i in range(3):
            user = UserController.GetUserByEmail('user_%d@hotmail.com' %i)
            token = UserController.GetUserToken(user)
            UserController.CompleteSignUp(None, user.User, token.Token, token.Type, user.username, user.email, user.Mobile , 1, datetime.date.today())
            self.assertEqual(user.User.is_active , True, "User User_%d couldn't be Activited." % i)

    def test_ValidateCredentials(self):
        for i in range(3):
            user = UserController.GetUserByEmail('user_%d@hotmail.com' % i)
            user = UserController.ValidateCredentials(user.username, '123')
            self.assertNotEqual(user, None, "Username User_%d couldn't be Validated." % i)

    def test_FollowUnFollow(self):
        for i in range(2):
            user1 = UserController.GetUserByEmail('user_%d@hotmail.com' %i)
            user2 = UserController.GetUserByEmail('user_%d@hotmail.com' % (i+1))

            UserController.FollowStream(None, user1, user2.Stream)
            res = user2.Stream in user1.Following.all()
            self.assertEqual(res, True, "User_%d cannot follow user_%d's stream " %(i, i+1))

            UserController.UnfollowStream(None, user1, user2.Stream)
            res = user2.Stream in user1.Following.all()
            self.assertEqual(res, False, "User_%d cannot unfollow user_%d's stream " %(i, i+1))

    def test_SearchUser(self):
        res = UserController.SearchUsers('Shouter_', 100)
        self.assertEqual(len(res), 3, "Search User didn't fitch all of them.")

    def test_UserFollowing(self):
        for i in range(3):
            user = UserController.GetUserByEmail('user_%d@hotmail.com' % i)
            followers = UserController.UserFollowers(user.username)
            self.assertEqual(len(followers), 0, "incorrect number of followers")

    def test_UserFollowers(self):
        for i in range(3):
            user = UserController.GetUserByEmail('user_%d@hotmail.com' % i)
            followings = UserController.UserFollowing(user.username, 'all', 'all')
            self.assertEqual(len(followings['stores']), 0, "incorrect number of store followings")
            self.assertEqual(len(followings['storesId']), 0, "incorrect number of followings")
            self.assertEqual(len(followings['users']), 0, "incorrect number of followings")
            self.assertEqual(len(followings['tags']), 0, "incorrect number of followings")


class ShoutTestCase(TestCase):
    def setUp(self):
        create_users()
        self.ids = []
        self.user = UserController.GetUserByEmail('user_0@hotmail.com')
        for i in range(3):
            shout_buy = ShoutController.shout_buy(None, 'Shout_Buy_%d' % i, 'this is shout__buy_%d' % i,
                                                 23.4 * i, 20.34234 + i, 50.423463 + i, ['tag_1', 'tag_2', 'tag_3', 'tag_4', 'tag_5', 'tag_6'],
                                                 self.user.User, 'AE', 'Dubai', '', 'aed')
            self.ids.append(shout_buy.id)
            shout_sell = ShoutController.shout_sell(None, 'Shout_sell_%d' % i, 'this is shout__sell_%d' % i,
                                                   19.8 * i, 20.2434 + i, 50.636 + i, ['tag_1', 'tag_2', 'tag_3', 'tag_4', 'tag_5', 'tag_6'],
                                                   self.user.User, 'AE', 'Dubai', '', 'aed')
            self.ids.append(shout_sell.id)
            self.assertNotEqual(shout_buy, None, 'Could not create shout_buy_%d' % i)
            self.assertNotEqual(shout_sell, None, 'Could not create shout_sell_%d' % i)

    def test_GetShout(self):
        shout = ShoutController.GetPost(self.ids[0])
        self.assertNotEqual(shout, None, 'Could not retrieve shout_buy_0')
        if shout:
            self.assertEqual(shout.Type, POST_TYPE_BUY, "Could not retrieve the correct shout: shout_buy_0")
            self.assertEqual(shout.Text, 'this is shout__buy_0', "Could not retrieve the correct shout: shout_buy_0")

        ShoutController.DeletePost(self.ids[1])
        shout = ShoutController.GetPost(self.ids[1])
        self.assertEqual(shout, None, 'Retrieve deleted shout')

    def test_DeleteShout(self):
        shout = ShoutController.GetPost(self.ids[2])
        shout = ShoutController.DeletePost(shout.id)
        self.assertEqual(shout.IsDisabled,True,"couldn't delete shout")


    #TODO: make a test function for ShoutController.GetStreamAffectedByShout
    #TODO: make a test function for ShoutController.TagsAffinity
    #TODO: make a test function for ShoutController.SaveRecolatedShouts

class TagTestCase(TestCase):
    def setUp(self):
        create_users()
        self.user = UserController.GetUserByEmail('user_0@hotmail.com')
        for i in range(50):
            TagController.GetOrCreateTag(None, 'Tag_%d' % i, self.user.User, None)
            tag = TagController.GetTag('Tag_%d' % i)
            self.assertNotEqual(tag, None, "Tag_%d was not found, it may has been created and not fetched or it hasn't been created at all" % i )

    def test_GetOrCreateTag(self):
        exist_tag = TagController.GetOrCreateTag(None, 'Tag_0', self.user.User, None)
        self.assertNotEqual(exist_tag, None, "Exist tag Tag_0 was not found")

        nonexist_tag = TagController.GetTag('Tag_99')
        self.assertEqual(nonexist_tag, None, "NonExist tag Tag_99 was found !!")

        nonexist_tag = TagController.GetOrCreateTag(None, 'Tag_99', self.user.User, None)
        self.assertNotEqual(nonexist_tag, None, "Newly created tag Tag_99 was not found")

        for i in range(100):
            tag = TagController.GetOrCreateTag(None, 'Tag_%d' % i, self.user.User, None)
            self.assertNotEqual(tag, None, "tag Tag_%d was not found nor created!" % i)

        tags = []
        for i in range(50,150):
            tags.append('Tag_%d' % i)
        created_tags = TagController.GetOrCreateTags(None, tags, self.user.User)
        self.assertEqual(len(tags), len(created_tags), "Not All tags created or found")

    def test_AddToUserInterests(self):
        user = UserController.GetUserByEmail('user_1@hotmail.com')
        tag = TagController.GetOrCreateTag(None, 'Tag_0', self.user.User, None)
        TagController.AddToUserInterests(None, tag, user.User)
        self.assertEqual(tag in list(user.Interests.all()), True, 'Tag_0 was not followed by User_1')

    def test_RemoveFromUserInterests(self):
        user = UserController.GetUserByEmail('user_2@hotmail.com')
        tag = TagController.GetOrCreateTag(None, 'Tag_1', self.user.User, None)

        TagController.AddToUserInterests(None, tag, user)
        self.assertEqual(tag in list(user.Interests.all()), True, 'Tag_1 was not followed by User_2')

        TagController.RemoveFromUserInterests(None, tag, user)
        self.assertEqual(tag in list(user.Interests.all()), False, 'Tag_1 was not unfollowed by User_2')

    def test_SearchTags(self):
        tags = TagController.SearchTags("Tag_",100)
        self.assertEqual(len(tags),50 ,'Not All related tags retrieve ')

    def test_TagFollowers(self):
        user = UserController.GetUserByEmail('user_1@hotmail.com')
        tag = TagController.GetOrCreateTag(None, 'Tag_0', self.user.User, None)
        TagController.AddToUserInterests(None, tag, user.User)

        tags = TagController.TagFollowers("Tag_0")
        self.assertEqual(len(tags),1 ,'Not All Followers retrieve')


class MessageTestCase(TestCase):
    def setUp(self):
        create_users()
        self.user1 = UserController.GetUserByEmail('user_0@hotmail.com').User
        self.user2 = UserController.GetUserByEmail('user_1@hotmail.com').User
        self.user3 = UserController.GetUserByEmail('user_2@hotmail.com').User
        self.post  = ShoutController.shout_buy(None, 'Shout', 'test shout',
                                              23.4, 20.34234 , 50.423463 , ['tag_1', 'tag_2', 'tag_3', 'tag_4', 'tag_5', 'tag_6'],
                                              self.user1, 'AE', 'Dubai', '')

    def test_ConversationExist(self):
        conversation = MessageController.ConversationExist(self.user1, self.user2, self.post)
        self.assertEqual(conversation,None,'Get conversation that is not existed')

        msg = MessageController.SendMessage(self.user2, self.user1, self.post, 'first message on ur post')
        retrieve_conversation = MessageController.ConversationExist(self.user1, self.user2, self.post)
        self.assertNotEqual(msg.Conversation,None,'Could not retrieve conversation From user2 to user1 on post')
        self.assertEqual(msg.Conversation,retrieve_conversation,'conversation retrieved wrong')

    def test_SendMessage(self):
        msg = MessageController.SendMessage(self.user2, self.user1, self.post, 'first message on ur post')
        self.assertNotEqual(msg,None,'Could not send msg')


    def test_ReadConversations(self):
        msgFromUser2 = MessageController.SendMessage(self.user2, self.user1, self.post, 'first From user2 message on ur post')
        msgFromUser3 = MessageController.SendMessage(self.user3, self.user1, self.post, 'first From user3 message on ur post')
        conversations = MessageController.ReadConversations(self.user1)
        self.assertEqual(len(conversations),2,'Could retrieve all user conversations')

        conversations = MessageController.ReadConversations(self.user2)
        self.assertEqual(len(conversations),1,'Retrieve wrong conversations')

    def test_ReadConversation(self):
        msg = MessageController.SendMessage(self.user2, self.user1, self.post, 'first From user2 message on ur post')
        msgs = MessageController.ReadConversation(self.user1, msg.Conversation.id,None)
        self.assertEqual(len(msgs),1,'Retrieve wrong messages')


    def test_GetConversation(self):
        msg = MessageController.SendMessage(self.user2, self.user1, self.post, 'first From user2 message on ur post')
        conversation = MessageController.GetConversation(msg.Conversation.id)
        self.assertNotEqual(conversation,None,'Conversation Could not retrieve')
        self.assertEqual(msg.Conversation,conversation,'Conversation retrieved wrong')

        conversation = MessageController.GetConversation(msg.Conversation.id,self.user1)
        self.assertNotEqual(conversation,None,'Conversation Could not retrieve for user 1')
        self.assertEqual(msg.Conversation,conversation,'Conversation retrieved wrong for user 1')

    def test_GetShoutConversations(self):
        msgFromUser2 = MessageController.SendMessage(self.user2, self.user1, self.post, 'first From user2 message on ur post')
        msgFromUser3 = MessageController.SendMessage(self.user3, self.user1, self.post, 'first From user3 message on ur post')
        conversations = MessageController.GetShoutConversations(self.post.id, self.user1)
        self.assertEqual(len(conversations),2,'Not All Conversations Retrieved')

        conversations = MessageController.GetShoutConversations(self.post.id, self.user2)
        self.assertNotEqual(conversations,None,'Conversation could not Retrieved')
        self.assertEqual(len(conversations),1,'Number of Conversations Retrieved Wrong')
        self.assertEqual(conversations[0],msgFromUser2.Conversation,'Conversation Retrieved Wrong')

    def test_DeleteMessage(self):
        msgFromUser2 = MessageController.SendMessage(self.user2, self.user1, self.post, 'first From user2 message on ur post')
        msgFromUser3 = MessageController.SendMessage(self.user3, self.user1, self.post, 'first From user3 message on ur post')
        msg2AccordingToUser1 = MessageController.DeleteMessage(self.user1,msgFromUser2.id)
        self.assertEqual(msg2AccordingToUser1.VisibleToRecivier,False,'Message could not deleted')
        msg2AccordingToUser2 = MessageController.GetMessage(msgFromUser2.id)
        self.assertEqual(msg2AccordingToUser2.VisibleToSender,True,'Wrong Message deleted')

    def test_DeleteConversation(self):
        msgFromUser2 = MessageController.SendMessage(self.user2, self.user1, self.post, 'first From user2 message on ur post')
        msgFromUser3 = MessageController.SendMessage(self.user3, self.user1, self.post, 'first From user3 message on ur post')
        conversation2AccordingToUser1 = MessageController.DeleteConversation(self.user1,msgFromUser2.Conversation.id)
        self.assertEqual(conversation2AccordingToUser1.VisibleToRecivier,False,'Conversation could not deleted')
        Conversation2AccordingToUser2 = MessageController.GetConversation(msgFromUser2.Conversation.id)
        self.assertEqual(Conversation2AccordingToUser2.VisibleToSender,True,'Wrong Conversation deleted')

