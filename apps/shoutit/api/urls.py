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


                    url(r'^activities_stream/(?:(\d+)/)?$',
                        TieredResource(TieredHandler, no_oauth, {
                            'GET': user_views.activities_stream
                        })
                    ),

                    # TODO: to look at: shoutit2
                    url(r'^experiences_stream/(?:(\d+)/)?$',
                        TieredResource(TieredHandler, no_oauth, {
                            'GET': experience_views.experiences_stream
                        })
                    ),
)

shout_api = patterns('',
                     url(r'^stream/',
                         TieredResource(TieredHandler, oauth, {
                             'GET': stream_views.index_stream,
                         })
                     ),

                     url(r'^nearby/$',
                         TieredResource(TieredHandler, oauth, {
                             'GET': shout_views.nearby_shouts
                         })
                     ),

                     url(r'^nearby/clusters/$',
                         TieredResource(TieredHandler, oauth, {
                             'GET': shout_views.load_clusters
                         })
                     ),

                     url(r'^buy/$',
                         TieredResource(TieredHandler, oauth, {
                             'POST': shout_views.post_request
                         })
                     ),

                     url(r'^sell/$',
                         TieredResource(TieredHandler, oauth, {
                             'POST': shout_views.post_offer
                         })
                     ),

                     url(r'^(?P<shout_id>[-\w]+)/', include(
                         patterns('',

                                  url(r'^$',
                                      TieredResource(TieredHandler, oauth, {
                                          'GET': shout_views.shout_view,
                                          'DELETE': shout_views.delete_shout,
                                          'POST': message_views.reply_to_shout
                                      })
                                  ),

                                  url(r'^messages/$',
                                      TieredResource(TieredHandler, oauth, {
                                          'GET': message_views.get_shout_conversations
                                      })
                                  ),

                         )
                     )),

                     # TODO: to look at: shoutit2
                     url(r'^experience/(?:(\w+)/)?$',
                         TieredResource(TieredHandler, oauth, {
                             'POST': experience_views.post_exp
                         })
                     ),
)

message_api = patterns('',
                       url(r'^$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': message_views.read_conversation,
                               'POST': message_views.reply_in_conversation,
                               'DELETE': message_views.delete_conversation
                           })
                       ),

                       # todo: read conversation, read message
                       url(r'^read/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': message_views.mark_message_as_read
                           })
                       ),

                       url(r'^(?P<message_id>[-\w]+)/$',
                           TieredResource(TieredHandler, oauth, {
                               'DELETE': message_views.delete_message
                           })
                       ),
)

tag_api = patterns('',
                   url(r'^$',
                       TieredResource(TieredHandler, oauth, {
                           'GET': tag_views.tag_profile
                       })
                   ),

                   url(r'^stream/$',
                       TieredResource(TieredHandler, oauth, {
                           'GET': tag_views.tag_stream
                       })
                   ),

                   url(r'^listeners/$',
                       TieredResource(TieredHandler, oauth, {
                           'GET': tag_views.tag_stats
                       })
                   ),

                   url(r'^listen/$',
                       TieredResource(TieredHandler, oauth, {
                           'POST': tag_views.start_listening_to_tag,
                           'DELETE': tag_views.stop_listening_to_tag
                       })
                   ),

                   url(r'^picture/$',
                       TieredResource(TieredHandler, oauth, {
                           'GET': general_views.profile_picture
                       }), {'profile_type': 'tag'}
                   ),
)

notification_api = patterns('',
                            url(r'^$',
                                TieredResource(TieredHandler, oauth, {
                                    'GET': realtime_views.notifications_all
                                })
                            ),

                            url(r'^count/$',
                                TieredResource(TieredHandler, oauth, {
                                    'GET': realtime_views.notifications_count
                                })
                            ),

                            url(r'^brief/$',
                                TieredResource(TieredHandler, oauth, {
                                    'GET': realtime_views.notifications
                                })
                            ),

                            # todo: check!
                            url(r'^(?P<notification_id>[-\w]+)/', include(
                                patterns('',
                                         url(r'^read/$',
                                             TieredResource(TieredHandler, oauth, {
                                                 'PUT': realtime_views.mark_notification_as_read
                                             })
                                         ),

                                         url(r'^unread/$',
                                             TieredResource(TieredHandler, oauth, {
                                                 'PUT': realtime_views.mark_notification_as_unread
                                             })
                                         ),

                                )
                            )),


)

urlpatterns = patterns('',
                       # Users

                       url(r'^users/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': user_views.search_user,
                               'PUT': user_views.user_edit_profile
                           })
                       ),

                       url(r'^users/link_(facebook|gplus)/$',
                           TieredResource(TieredHandler, oauth, {
                               'POST': relink_social_channel,
                               'DELETE': relink_social_channel
                           })
                       ),

                       url(r'^users/(?P<username>@me|[\w.]+)/', include(user_api)),


                       # Shouts

                       url(r'^shouts/', include(shout_api)),


                       # Messages

                       url(r'^messages/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': message_views.read_conversations_stream
                           })
                       ),

                       url(r'^messages/(?P<conversation_id>[-\w]+)/', include(message_api)),


                       # Tags

                       url(r'^tags/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': tag_views.search_tag
                           })
                       ),

                       url(r'^tags/(?P<tag_name>[a-z0-9-]+)/', include(tag_api)),


                       url(r'^top_tags/$',
                           TieredResource(TieredHandler, oauth, {
                               'GET': tag_views.top_tags
                           })
                       ),


                       # Notifications

                       url(r'^notifications/', include(notification_api)),

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

                       url(r'^categories/$',
                           TieredResource(TieredHandler, no_oauth, {
                               'GET': general_views.categories
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


                       url(r'^experiences/([-\w]+)/$',
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