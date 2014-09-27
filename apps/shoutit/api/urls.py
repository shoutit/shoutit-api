from django.conf.urls import patterns, url
from piston3.resource import Resource
from piston3.authentication import OAuthAuthentication, NoAuthentication
from apps.shoutit.tiered_views import user_views, realtime_views, tag_views, stream_views, shout_views, message_views
from apps.shoutit.tiered_views import general_views, experience_views, comment_views, business_views

from apps.shoutit.api.handlers import *


class TieredResource(Resource):
    def __init__(self, handler, authentication=None, methods_map=None):
        if not methods_map:
            methods_map = {}
        super(TieredResource, self).__init__(handler, authentication)
        self.csrf_exempt = getattr(self.handler, 'csrf_exempt', True)
        self.handler.methods_map = methods_map

    def __call__(self, request, *args, **kwargs):
        request.is_api = True
        return Resource.__call__(self, request, *args, **kwargs)


class MethodDependentAuthentication(object):
    def __init__(self, methods_auth_map=None, default=None):
        if not methods_auth_map:
            methods_auth_map = {}
        self.methods_auth_map = methods_auth_map
        self.default = default
        self.last_request = None

    def is_authenticated(self, request):
        self.last_request = request
        if request.method in self.methods_auth_map.keys():
            return self.methods_auth_map[request.method].is_authenticated(request)
        elif self.default:
            return self.default(request)
        else:
            return False

    def challenge(self):
        if self.last_request.method in self.methods_auth_map.keys():
            return self.methods_auth_map[self.last_request.method].challenge()
        elif self.default and hasattr(self.default, 'challenge'):
            return self.default.challenge()
        else:
            return None


o_auth = OAuthAuthentication()
a_oauth = NoAuthentication()

urlpatterns = patterns('',
                       url(r'^session/([0-9a-z]{32})/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': realtime_views.get_session_data,
                           })
                       ),

                       url(r'^session/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': realtime_views.get_session_data,
                           })
                       ),

                       url(r'^shouts/stream/(?:(\d+)/)?',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': stream_views.index_stream,
                           })
                       ),

                       url(r'^shouts/nearby/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': stream_views.load_shouts
                           })
                       ),

                       url(r'^shouts/nearby/clusters/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': stream_views.load_clusters
                           })
                       ),

                       url(r'^tag/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': tag_views.search_tag,
                           })
                       ),

                       url(r'^tag/([^/]+)/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': tag_views.tag_profile,
                           })
                       ),

                       url(r'^tag/([^/]+)/brief/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': tag_views.tag_profile_brief,
                           })
                       ),

                       url(r'^tag/([^/]+)/stats/(\w+)/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': tag_views.tag_stats,
                           })
                       ),

                       url(r'^tag/([^/]+)/follow/$',
                           TieredResource(TieredHandler, o_auth, {
                               'POST': tag_views.add_tag_to_interests,
                               'DELETE': tag_views.remove_tag_from_interests,
                           })
                       ),

                       url(r'^tag/([^/]+)/stream/(?:(\d+)/)?$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': tag_views.tag_stream,
                           })
                       ),

                       url(r'^(tag)/([^/]+)/picture(?:/(\d+))?/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': general_views.profile_picture,
                           })
                       ),

                       url(r'^user/search/(\w+)/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': user_views.search_user,
                           })
                       ),

                       url(r'^user/(@me|\w+)/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': user_views.user_profile,
                           })
                       ),

                       url(r'^user/(@me|\w+)/brief/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': user_views.user_profile_brief,
                           })
                       ),

                       url(r'^user/(@me|\w+)/stats/(\w+)(?:/(\w+))?(?:/(\w+))?/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': user_views.user_stats,
                           })
                       ),

                       url(r'^(user)/(@me|\w+)/picture(?:/(\d+))?/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': general_views.profile_picture,
                           })
                       ),

                       url(r'^user/(\w+)/follow/$',
                           TieredResource(TieredHandler, o_auth, {
                               'POST': user_views.follow_user,
                               'DELETE': user_views.unfollow_user
                           })
                       ),

                       url(r'^user/(@me|\w+)/stream/(?:(\d+)/)?$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': user_views.user_stream,
                           })
                       ),

                       url(r'^user/(@me|\w+)/stats/(\w+)(?:/(\w+))?(?:/(\w+))?/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': user_views.user_stats,
                           })
                       ),

                       # TODO: deprecate?
                       url(r'^signup/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'POST': user_views.signup,
                           })
                       ),

                       url(r'^notifications/brief/$',
                           TieredResource(TieredHandler, o_auth, {
                               'GET': realtime_views.notifications
                           })
                       ),

                       url(r'^notifications/all/$',
                           TieredResource(TieredHandler, o_auth, {
                               'GET': realtime_views.notifications_all
                           })
                       ),

                       url(r'^unread_notifications_count/$',
                           TieredResource(TieredHandler, o_auth, {
                               'GET': realtime_views.unread_notifications_count
                           })
                       ),

                       url(r'^notification/(\w+)/read/$',
                           TieredResource(TieredHandler, o_auth, {
                               'POST': realtime_views.mark_notification_as_read,
                           })
                       ),

                       url(r'^notification/(\w+)/unread/$',
                           TieredResource(TieredHandler, o_auth, {
                               'POST': realtime_views.mark_notification_as_unread,
                           })
                       ),

                    # Shouts: create, edit, delete, reply
                       url(r'^shout/buy/$',
                           TieredResource(TieredHandler, o_auth, {
                               'POST': shout_views.shout_buy,
                           })
                       ),

                       url(r'^shout/sell/$',
                           TieredResource(TieredHandler, o_auth, {
                               'POST': shout_views.shout_sell,
                           })
                       ),

                       url(r'^shout/experience/(?:(\w+)/)?$',
                           TieredResource(TieredHandler, o_auth, {
                               'POST': experience_views.post_exp,
                           })
                       ),

                       url(r'^shout/([0-9a-zA-Z]+)/$',
                           TieredResource(TieredHandler, MethodDependentAuthentication({'GET': a_oauth, 'POST': o_auth, 'DELETE': o_auth}),
                                          {
                                              'GET': shout_views.shout_view,
                                              'DELETE': shout_views.delete_shout,
                                              'POST': message_views.reply_to_shout,
                                          })
                       ),

                       url(r'^shout/([0-9a-zA-Z]+)/brief/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': shout_views.load_shout,
                           })
                       ),

                       url(r'^shout/([0-9a-zA-Z]+)/messages/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': message_views.get_shout_conversations,
                           })
                       ),

                       url(r'^upload/([\w_-]+)/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'POST': shout_views.cloud_upload,
                           })
                       ),

                       url(r'^messages/(?:(\d+)/)?$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': message_views.read_conversations_stream
                           })
                       ),

                       url(r'^message/([a-zA-z0-9]+)/$',
                           TieredResource(TieredHandler, o_auth, {
                               'GET': message_views.read_conversation,
                               'POST': message_views.reply_to_conversation,
                           })
                       ),

                       url(r'^message/(\w+)/read/$',
                           TieredResource(TieredHandler, o_auth, {
                               'POST': message_views.mark_message_as_read,
                           })
                       ),

                       url(r'^notify/([^/]+)/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': realtime_views.send_fake_notification,
                           })
                       ),

                       url(r'^currencies/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': general_views.currencies,
                           })
                       ),

                       url(r'^business_categories/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': business_views.business_categories
                           })
                       ),

                       url(r'^apns_token/([0-9a-f]+)/$',
                           TieredResource(TieredHandler, o_auth, {
                               'POST': realtime_views.add_apns_token,
                               'DELETE': realtime_views.remove_apns_token,
                           })
                       ),

                       url(r'^sss/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'POST': user_views.sss,
                           })
                       ),

                       #TODO: deprecate?
                       url(r'^fb_auth/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'POST': user_views.fb_auth,
                           })
                       ),

                       #TODO: deprecate?
                       url(r'^gplus_auth/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'POST': user_views.gplus_auth,
                           })
                       ),

                       url(r'^location/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'POST': user_views.set_user_session_location_info,
                           })
                       ),

                       #TODO: deprecate?
                       url(r'^activate/([abcdefghklmnopqrstuvwxyzABCDEFGHKLMNPQRSTUVWXYZ23456789]*)/$',
                           TieredResource(TieredHandler, o_auth, {
                               'POST': user_views.activate_api,
                           })
                       ),

                       #shoutit2
                       url(r'^user/(@me|\w+)/experiences_stream/(?:(\d+)/)?$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': experience_views.experiences_stream,
                           })
                       ),

                       url(r'^user/(@me|\w+)/activities_stream/(?:(\d+)/)?$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': user_views.activities_stream,
                           })
                       ),

                       url(r'^experience/([0-9a-zA-Z]+)/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': experience_views.view_experience,
                           })
                       ),

                       url(r'^post_comments/([0-9a-zA-Z]+)/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'GET': comment_views.post_comments,
                           })
                       ),

                       url(r'^comment_on_post/([0-9a-zA-Z]+)/$',
                           TieredResource(TieredHandler, a_oauth, {
                               'POST': comment_views.comment_on_post,
                           })
                       ),
)