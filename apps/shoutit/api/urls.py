from django.conf.urls import patterns, url
from piston3.resource import Resource
from piston3.authentication import OAuthAuthentication, NoAuthentication
from apps.shoutit.tiered_views import user_views, realtime_views, tag_views, stream_views, shout_views, message_views
from apps.shoutit.tiered_views import general_views, experience_views, comment_views, business_views

from apps.shoutit.api.handlers import TieredHandler


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
    # Example
    # MethodDependentAuthentication({'GET': no_oauth, 'POST': oauth, 'DELETE': oauth})

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

oauth = OAuthAuthentication()
no_oauth = NoAuthentication()

urlpatterns = patterns('',
                       # Users

                       url(r'^user/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': user_views.search_user
                           })
                       ),

                       url(r'^user/(@me|\w+)/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': user_views.user_profile
                           })
                       ),

                       url(r'^user/(@me|\w+)/brief/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': user_views.user_profile_brief
                           })
                       ),

                       url(r'^user/(@me|\w+)/listen/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': user_views.start_listening_to_user,
                               'DELETE': user_views.stop_listening_to_user
                           })
                       ),

                       url(r'^user/(@me|\w+)/(listening|listeners)/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': user_views.user_stats
                           })
                       ),

                       url(r'^user/(@me|\w+)/(listening)/(users|tags|all)/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': user_views.user_stats
                           })
                       ),

                       url(r'^user/(@me|\w+)/(listening)/(users|tags|all)/(recent|all)/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': user_views.user_stats
                           })
                       ),

                       url(r'^user/(@me|\w+)/stream/?$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': user_views.user_stream
                           })
                       ),

                       url(r'^(user)/(@me|\w+)/picture(?:/(\d+))?/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': general_views.profile_picture
                           })
                       ),


                       # Shouts

                       url(r'^shout/stream/',
                           TieredResource(TieredHandler, oauth, {
                               'GET': stream_views.index_stream,
                           })
                       ),

                       url(r'^shout/nearby/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': stream_views.load_shouts
                           })
                       ),

                       url(r'^shout/nearby/clusters/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': stream_views.load_clusters
                           })
                       ),

                       url(r'^shout/buy/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': shout_views.shout_buy
                           })
                       ),

                       url(r'^shout/sell/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': shout_views.shout_sell
                           })
                       ),

                       url(r'^shout/experience/(?:(\w+)/)?$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': experience_views.post_exp
                           })
                       ),

                       url(r'^shout/([0-9a-zA-Z]+)/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': shout_views.shout_view,
                               'DELETE': shout_views.delete_shout,
                               'POST': message_views.reply_to_shout
                           })
                       ),

                       url(r'^shout/([0-9a-zA-Z]+)/brief/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': shout_views.load_shout
                           })
                       ),

                       url(r'^shout/([0-9a-zA-Z]+)/messages/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': message_views.get_shout_conversations
                           })
                       ),


                       # Messages

                       url(r'^messages/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': message_views.read_conversations_stream
                           })
                       ),

                       url(r'^messages/([a-zA-z0-9]+)/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': message_views.read_conversation,
                               'POST': message_views.reply_in_conversation
                           })
                       ),

                       url(r'^messages/(\w+)/read/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': message_views.mark_message_as_read
                           })
                       ),


                       # Tags

                       url(r'^tag/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': tag_views.search_tag
                           })
                       ),

                       url(r'^tag/([^/]+)/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': tag_views.tag_profile
                           })
                       ),

                       url(r'^tag/([^/]+)/brief/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': tag_views.tag_profile_brief
                           })
                       ),

                       url(r'^tag/([^/]+)/listeners/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': tag_views.tag_stats
                           })
                       ),

                       url(r'^tag/([^/]+)/listen/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': tag_views.start_listening_to_tag,
                               'DELETE': tag_views.stop_listening_to_tag
                           })
                       ),

                       url(r'^tag/([^/]+)/stream/?$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': tag_views.tag_stream
                           })
                       ),

                       url(r'^(tag)/([^/]+)/picture(?:/(\d+))?/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': general_views.profile_picture
                           })
                       ),


                       # Notifications

                       url(r'^notifications/brief/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': realtime_views.notifications
                           })
                       ),

                       url(r'^notifications/all/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': realtime_views.notifications_all
                           })
                       ),

                       url(r'^unread_notifications_count/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': realtime_views.unread_notifications_count
                           })
                       ),

                       url(r'^notification/(\w+)/read/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': realtime_views.mark_notification_as_read
                           })
                       ),

                       url(r'^notification/(\w+)/unread/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': realtime_views.mark_notification_as_unread
                           })
                       ),

                       url(r'^notify/([^/]+)/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': realtime_views.send_fake_notification
                           })
                       ),


                       # Misc

                       url(r'^upload/([\w_-]+)/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'POST': shout_views.upload_image
                           })
                       ),

                       url(r'^currencies/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': general_views.currencies
                           })
                       ),

                       url(r'^push/(apns|gcm)/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': user_views.push,
                               'POST': user_views.push,
                               'DELETE': user_views.push
                           })
                       ),

                       url(r'^update_location/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': user_views.update_user_location
                           })
                       ),
                       url(r'^business_categories/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': business_views.business_categories
                           })
                       ),

                       url(r'^session/([0-9a-z]{32})/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': realtime_views.get_session_data,
                           })
                       ),

                       url(r'^sss/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'POST': user_views.sss
                           })
                       ),

                       # TODO: deprecate?
                       url(r'^session/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': realtime_views.get_session_data,
                           })
                       ),

                       # TODO: deprecate?
                       url(r'^apns_token/([0-9a-f]+)/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': realtime_views.add_apns_token,
                               'DELETE': realtime_views.remove_apns_token
                           })
                       ),

                       # TODO: deprecate?
                       url(r'^signup/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'POST': user_views.signup,
                           })
                       ),

                       # TODO: deprecate?
                       url(r'^fb_auth/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'POST': user_views.fb_auth
                           })
                       ),

                       #TODO: deprecate?
                       url(r'^gplus_auth/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'POST': user_views.gplus_auth
                           })
                       ),

                       #TODO: deprecate?
                       url(r'^activate/([abcdefghklmnopqrstuvwxyzABCDEFGHKLMNPQRSTUVWXYZ23456789]*)/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': user_views.activate_api
                           })
                       ),


                       # TODO: to look at: shoutit2

                       url(r'^user/(@me|\w+)/experiences_stream/(?:(\d+)/)?$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': experience_views.experiences_stream
                           })
                       ),

                       url(r'^user/(@me|\w+)/activities_stream/(?:(\d+)/)?$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': user_views.activities_stream
                           })
                       ),

                       url(r'^experience/([0-9a-zA-Z]+)/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': experience_views.view_experience
                           })
                       ),

                       url(r'^post_comments/([0-9a-zA-Z]+)/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': comment_views.post_comments
                           })
                       ),

                       url(r'^comment_on_post/([0-9a-zA-Z]+)/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'POST': comment_views.comment_on_post
                           })
                       ),
)