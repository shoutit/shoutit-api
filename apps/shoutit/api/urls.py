from django.conf.urls import include, patterns, url
from piston3.resource import Resource
from piston3.authentication import OAuthAuthentication, NoAuthentication
from apps.shoutit.api.authentication import relink_social_channel
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
        self.handler.allowed_methods = methods_map.keys()

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

user_api = patterns('',
                    url(r'^$',
                        TieredResource(TieredHandler, oauth, {
                            'GET': user_views.user_profile
                        })
                    ),

                    url(r'^brief/$',
                        TieredResource(TieredHandler, oauth, {
                            'GET': user_views.user_profile_brief
                        })
                    ),

                    url(r'^listen/$',
                        TieredResource(TieredHandler, oauth, {
                            'POST': user_views.start_listening_to_user,
                            'DELETE': user_views.stop_listening_to_user
                        })
                    ),

                    url(r'^(?P<stats_type>listening|listeners)/$',
                        TieredResource(TieredHandler, oauth, {
                            'GET': user_views.user_stats
                        })
                    ),

                    url(r'^(?P<stats_type>listening)/(?P<listening_type>users|tags|all)/$',
                        TieredResource(TieredHandler, oauth, {
                            'GET': user_views.user_stats
                        })
                    ),

                    url(r'^(?P<stats_type>listening)/(?P<listening_type>users|tags|all)/(?P<period>recent|all)/$',
                        TieredResource(TieredHandler, oauth, {
                            'GET': user_views.user_stats
                        })
                    ),

                    url(r'^stream/?$',
                        TieredResource(TieredHandler, oauth, {
                            'GET': user_views.user_stream
                        })
                    ),

                    url(r'^picture/$',
                        TieredResource(TieredHandler, oauth, {
                            'GET': general_views.profile_picture
                        }), {'profile_type': 'user'}
                    ),

                    url(r'^video/$',
                        TieredResource(TieredHandler, oauth, {
                            'GET': user_views.user_video,
                            'POST': user_views.user_video,
                            'DELETE': user_views.user_video,
                        })
                    ),


                    # TODO: to look at: shoutit2
                    url(r'^experiences_stream/(?:(\d+)/)?$',
                        TieredResource(TieredHandler, no_oauth, {
                            'GET': experience_views.experiences_stream
                        })
                    ),

                    url(r'^activities_stream/(?:(\d+)/)?$',
                        TieredResource(TieredHandler, no_oauth, {
                            'GET': user_views.activities_stream
                        })
                    ),
)

urlpatterns = patterns('',
                       # Users

                       url(r'^user/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': user_views.search_user,
                               'PUT': user_views.user_edit_profile
                           })
                       ),

                       url(r'^user/link_(facebook|gplus)/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': relink_social_channel,
                               'DELETE': relink_social_channel
                           })
                       ),

                       url(r'^user/(?P<username>@me|[\w.]+)/', include(user_api)),


                       # Shouts

                       url(r'^shout/stream/',
                           TieredResource(TieredHandler, oauth, {
                               'GET': stream_views.index_stream,
                           })
                       ),

                       url(r'^shout/nearby/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': shout_views.nearby_shouts
                           })
                       ),

                       url(r'^shout/nearby/clusters/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': shout_views.load_clusters
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

                       url(r'^shout/([-\w]+)/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': shout_views.shout_view,
                               'DELETE': shout_views.delete_shout,
                               'POST': message_views.reply_to_shout2
                           })
                       ),

                       url(r'^shout/([-\w]+)/brief/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': shout_views.load_shout
                           })
                       ),

                       url(r'^shout/([-\w]+)/messages/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': message_views.get_shout_conversations
                           })
                       ),


                       # Messages

                       url(r'^messages/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': message_views.user_conversations
                           })
                       ),

                       url(r'^messages/([-\w]+)/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': message_views.read_conversation2,
                               'POST': message_views.reply_in_conversation2,
                               'DELETE': message_views.delete_conversation2
                           })
                       ),


                       url(r'^messages/([-\w]+)/([-\w]+)/$',
                           TieredResource(TieredHandler, oauth, {
                               'DELETE': message_views.delete_message2
                           })
                       ),

                       url(r'^messages/([-\w]+)/([-\w]+)/read/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': message_views.read_message2,
                               'DELETE': message_views.unread_message2
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

                       url(r'^top_tags/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': tag_views.top_tags
                           })
                       ),


                       # Notifications

                       url(r'^notifications/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': realtime_views.notifications_all
                           })
                       ),

                       url(r'^notifications/count/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': realtime_views.notifications_count
                           })
                       ),

                       url(r'^notifications/brief/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': realtime_views.notifications
                           })
                       ),

                       url(r'^notifications/([-\w]+)/read/$',
                           TieredResource(TieredHandler, oauth, {
                               'PUT': realtime_views.mark_notification_as_read
                           })
                       ),

                       url(r'^notifications/([-\w]+)/unread/$',
                           TieredResource(TieredHandler, oauth, {
                               'PUT': realtime_views.mark_notification_as_unread
                           })
                       ),

                       url(r'^notify/([^/]+)/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': realtime_views.send_fake_notification
                           })
                       ),


                       # Misc

                       url(r'^upload/([\w]+)/$',
                           TieredResource(TieredHandler, oauth, {
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

                       url(r'^sss4/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'POST': shout_views.shout_sss4
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

                       # TODO: deprecate?
                       url(r'^gplus_auth/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'POST': user_views.gplus_auth
                           })
                       ),

                       # TODO: deprecate?
                       url(r'^activate/([abcdefghklmnopqrstuvwxyzABCDEFGHKLMNPQRSTUVWXYZ23456789]*)/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': user_views.activate_api
                           })
                       ),


                       url(r'^experience/([-\w]+)/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': experience_views.view_experience
                           })
                       ),

                       url(r'^post_comments/([-\w]+)/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': comment_views.post_comments
                           })
                       ),

                       url(r'^comment_on_post/([-\w]+)/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'POST': comment_views.comment_on_post
                           })
                       ),

                       # inbound
                       url(r'^in/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': shout_views.inbound_email,
                               'POST': shout_views.inbound_email
                           })
                       ),

)