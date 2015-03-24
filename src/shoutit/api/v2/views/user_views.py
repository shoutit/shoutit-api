# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework_extensions.mixins import DetailSerializerMixin
from shoutit.api.v2.pagination import ShoutitPageNumberPagination, ShoutitPaginationMixin, ReverseDateTimePagination

from shoutit.controllers import stream_controller, message_controller

from shoutit.api.v2.serializers import *
from shoutit.api.v2.permissions import IsOwnerModify
from shoutit.controllers.facebook_controller import link_facebook_account, unlink_facebook_user
from shoutit.controllers.gplus_controller import link_gplus_account, unlink_gplus_user


class UserViewSet(DetailSerializerMixin, ShoutitPaginationMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    User API Resource.
    """
    lookup_field = 'username'

    serializer_class = UserSerializer
    serializer_detail_class = UserDetailSerializer

    queryset = User.objects.all()
    queryset_detail = User.objects.all().prefetch_related('profile')

    pagination_class = ShoutitPageNumberPagination

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('username', 'email')
    search_fields = ('=id', 'username', 'first_name', 'last_name', '=email')

    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerModify)

    def get_object(self):
        username = self.kwargs.get(self.lookup_field)
        if username == 'me' and self.request.user.is_authenticated():
            self.kwargs[self.lookup_field] = self.request.user.username

        return super(UserViewSet, self).get_object()

    def list(self, request, *args, **kwargs):
        """
        Get users based on `search` query param.

        ###Response
        <pre><code>
        {
          "count": 7, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {UserSerializer}
        }
        </code></pre>

        ---
        serializer: UserSerializer
        parameters:
            - name: search
              paramType: query
        """
        return super(UserViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Get user

        ---
        serializer: UserDetailSerializer
        parameters:
            - name: username
              description: me for logged in user
              paramType: path
              required: true
              defaultValue: me
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Modify user

        ###Request
        Specify any or all of these attributes to change them.

        <pre><code>
        {
            "username": "mo",
            "email": "mo.chawich@gmail.com",
            "first_name": "Mo",
            "last_name": "Chawich",
            "bio": "I'm a good shouter",
            "sex": 1,
            "image": "http://2ed106c1d72e039a6300-f673136b865c774b4127f2d581b9f607.r83.cf5.rackcdn.com/1NHUqCeh94NaWb8hlu74L7.jpg",
            "location": {
                "latitude": 25.1593957,
                "country": "AE",
                "longitude": 55.2338326,
                "city": "Dubai"
            },
            "video": {
                "url": "https://www.youtube.com/watch?v=Mp12bkOzO9Q",
                "thumbnail_url": "https://i.ytimg.com/vi/jXa4QfICnOg/default.jpg",
                "provider": "youtube",
                "id_on_provider": "Mp12bkOzO9Q",
                "duration": 12
            },
            "push_tokens": {
                "apns": "56yhnjflsdjfirjeoifjsorj4o",
                "gcm": "asjkdhsakjdhi3uhekndkjadkjsak"
            }
        }
        </code></pre>

        ####Deleting video and/or push_tokens
        <pre><code>
        {
            "video": null,
            "push_tokens": {
                "apns": null,
                "gcm": null
            }
        }
        </code></pre>

        ---
        serializer: UserDetailSerializer
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in user
              paramType: path
              required: true
              defaultValue: me
            - name: body
              paramType: body
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete user and everything attached to him

        ```
        NOT YET IMPLEMENTED
        ```

        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in user
              paramType: path
              required: true
              defaultValue: me
        """
        user = self.get_object()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['put'], suffix='Image')
    def image(self, request, *args, **kwargs):
        """
        Modify user image

        ###Request
        image url in json body
        <pre><code>
        {
            "image": "http://2ed106c1d72e039a6300-f673136b865c774b4127f2d581b9f607.r83.cf5.rackcdn.com/1NHUqCeh94NaWb8hlu74L7.jpg"
        }
        </code></pre>

        or

        <pre><code>
        PUT request with attached image file named `image_file`
        </pre></code>

        ---
        serializer: UserDetailSerializer
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in user
              paramType: path
              required: true
              defaultValue: me
            - name: image_file
              type: file
        """
        return self.partial_update(request, *args, **kwargs)

    @detail_route(methods=['post', 'delete'], suffix='Listen', permission_classes=(permissions.IsAuthenticatedOrReadOnly,))
    def listen(self, request, *args, **kwargs):
        """
        Start/Stop listening to user

        ###Listen
        <pre><code>
        POST: /v2/users/{username}/listen
        </code></pre>

        ###Stop listening
        <pre><code>
        DELETE: /v2/users/{username}/listen
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        user = self.get_object()
        profile = user.profile

        if request.user == user:
            raise ValidationError({'error': "You can not listen to your self"})

        if request.method == 'POST':
            stream_controller.listen_to_stream(request.user, profile.stream2)
            msg = "you started listening to {} shouts.".format(user.name)

        else:
            stream_controller.remove_listener_from_stream(request.user, profile.stream2)
            msg = "you stopped listening to {} shouts.".format(user.name)

        ret = {
            'data': {'success': msg},
            'status': status.HTTP_201_CREATED if request.method == 'POST' else status.HTTP_202_ACCEPTED
        }

        return Response(**ret)

    @detail_route(methods=['get'], suffix='Listeners')
    def listeners(self, request, *args, **kwargs):
        """
        Get user listeners

        ###Response
        <pre><code>
        {
          "count": 4, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {UserSerializer}
        }
        </code></pre>
        ---
        serializer: UserSerializer
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in user
              paramType: path
              required: true
              defaultValue: me
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        user = self.get_object()
        listeners = stream_controller.get_stream_listeners(user.profile.stream2)
        page = self.paginate_queryset(listeners)
        serializer = UserSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Listening')
    def listening(self, request, *args, **kwargs):
        """
        Get user listening based on `type` query param. It could be either 'users' or 'tags', default is 'users'

        ###Response
        <pre><code>
        {
          "count": 4, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {UserSerializer} same as in listeners or {TagSerializer}
        }
        </code></pre>

        ---
        serializer: TagSerializer
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in user
              paramType: path
              required: true
              defaultValue: me
            - name: type
              description:
              paramType: query
              required: true
              defaultValue: users
              enum:
                - users
                - tags
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """

        listening_type = request.query_params.get('type', 'users')
        if listening_type not in ['users', 'tags']:
            raise ValidationError({'type': "should be `users` or `tags`."})

        user = self.get_object()
        listening = stream_controller.get_user_listening_qs(user, listening_type)

        # we do not use the view pagination class since we need one with custom results field
        self.pagination_class = self.get_custom_shoutit_page_number_pagination_class(custom_results_field=listening_type)
        page = self.paginate_queryset(listening)

        result_object_serializers = {
            'users': UserSerializer,
            'tags': TagSerializer,
        }
        result_object_serializer = result_object_serializers[listening_type]
        serializer = result_object_serializer(page, many=True)

        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Shouts')
    def shouts(self, request, *args, **kwargs):
        """
        Get user shouts

        [Shouts Pagination](https://docs.google.com/document/d/1Zp9Ks3OwBQbgaDRqaULfMDHB-eg9as6_wHyvrAWa8u0/edit#heading=h.26dyymkevc5m)
        ---
        serializer: TradeSerializer
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in user
              paramType: path
              required: true
              defaultValue: me
            - name: shout_type
              paramType: query
              defaultValue: all
              enum:
                - request
                - offer
                - all
            - name: before
              description: timestamp to get shouts before
              paramType: query
            - name: after
              description: timestamp to get shouts after
              paramType: query
            - name: page_size
              paramType: query
        """
        shout_type = request.query_params.get('shout_type', 'all')
        if shout_type not in ['offer', 'request', 'all']:
            raise ValidationError({'shout_type': "should be `offer`, `request` or `all`."})

        user = self.get_object()
        trades = stream_controller.get_stream2_trades_qs(user.profile.stream2, shout_type)
        self.pagination_class = ReverseDateTimePagination
        page = self.paginate_queryset(trades)
        serializer = TradeSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['post'], suffix='Message')
    def message(self, request, *args, **kwargs):
        """
        Send user a message

        > A user can only message his Listeners, or someone whom he already have an existing conversation with.

        ###Request
        <pre><code>
        {
            "text": "text goes here",
            "attachments": [
                {
                    "shout": {
                        "id": ""
                    }
                },
                {
                    "location": {
                        "latitude": 12.345,
                        "longitude": 12.345
                    }
                }
            ]
        }
        </code></pre>

        ---
        response_serializer: MessageSerializer
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        user = self.get_object()
        if request.user == user:
            raise ValidationError({'error': "You can not start a conversation with your self"})
        if not (
            message_controller.conversation2_exist(users=[user, request.user]) or user.profile.is_listener(request.user.profile.stream2)
        ):
            raise ValidationError({'error': "You can only start a conversation with your listeners"})

        serializer = MessageSerializer(data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data['text']
        attachments = serializer.validated_data['attachments']
        message = message_controller.send_message2(conversation=None, user=request.user,
                                                   to_users=[user], text=text, attachments=attachments)
        message = MessageSerializer(instance=message, context={'request': request})
        headers = self.get_success_message_headers(message.data)
        return Response(message.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_message_headers(self, data):
        return {'Location': reverse('conversation-messages', kwargs={'id': data['conversation_id']}, request=self.request)}

    @detail_route(methods=['put', 'delete'], suffix='Link / Unlink Accounts')
    def link(self, request, *args, **kwargs):
        """
        Link/Unlink external social accounts

        ###Link Facebook
        <pre><code>
        PUT: /v2/users/{username}/link
        {
            "account": "facebook",
            "facebook_access_token": "facebook access token"
        }
        </code></pre>

        ###Unlink Facebook
        <pre><code>
        DELETE: /v2/users/{username}/link
        {
            "account": "facebook"
        }
        </code></pre>

        ###Link G+
        <pre><code>
        PUT: /v2/users/{username}/link
        {
            "account": "gplus",
            "gplus_code": "google grant code"
        }
        </code></pre>

        ###Unlink G+
        <pre><code>
        DELETE: /v2/users/{username}/link
        {
            "account": "gplus"
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: body
              paramType: body
        """
        user = self.get_object()
        account = request.data.get('account')
        if account not in ['facebook', 'gplus']:
            raise ValidationError({'account': "unsupported account"})

        if request.method == 'PUT':
            if account == 'gplus':
                gplus_code = request.data.get('gplus_code')
                if not gplus_code:
                    raise ValidationError({'gplus_code': "please provide valid google plus code"})
                link_gplus_account(user, gplus_code, hasattr(request.auth, 'client') and request.auth.client or None)

            if account == 'facebook':
                facebook_access_token = request.data.get('facebook_access_token')
                if not facebook_access_token:
                    raise ValidationError({'facebook_access_token': "please provide valid facebook access token"})
                link_facebook_account(user, facebook_access_token)

            msg = "{} linked successfully.".format(account)

        else:
            if account == 'gplus':
                unlink_gplus_user(user)

            if account == 'facebook':
                unlink_facebook_user(user)

            msg = "{} unlinked successfully.".format(account)

        ret = {
            'data': {'success': msg},
            'status': status.HTTP_202_ACCEPTED
        }

        return Response(**ret)
