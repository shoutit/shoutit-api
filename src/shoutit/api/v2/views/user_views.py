# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import viewsets, filters, status, mixins
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework.reverse import reverse
from rest_framework_extensions.mixins import DetailSerializerMixin

from shoutit.api.v2.filters import HomeFilterBackend
from shoutit.api.v2.pagination import (
    ShoutitPaginationMixin, PageNumberIndexPagination, ShoutitPageNumberPaginationNoCount
)
from shoutit.controllers import listen_controller, message_controller, facebook_controller, gplus_controller
from shoutit.api.v2.serializers import (
    UserSerializer, UserDetailSerializer, MessageSerializer, TagSerializer, ShoutSerializer
)
from shoutit.api.v2.permissions import IsOwnerModify, IsAuthenticatedOrReadOnly, IsAuthenticated, IsOwner
from shoutit.models import User, Shout, ShoutIndex


class UserViewSet(DetailSerializerMixin, ShoutitPaginationMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    User API Resource.
    """
    lookup_field = 'username'
    lookup_value_regex = '[0-9a-zA-Z._]+'

    serializer_class = UserSerializer
    serializer_detail_class = UserDetailSerializer

    queryset = User.objects.filter(is_activated=True)
    queryset_detail = User.objects.filter().prefetch_related('profile')

    pagination_class = ShoutitPageNumberPaginationNoCount

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('username', 'email')
    search_fields = ('=id', 'username', 'first_name', 'last_name', '=email')

    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerModify)

    def get_object(self):
        username = self.kwargs.get(self.lookup_field)
        if self.request.user.is_authenticated():
            if username == 'me' or username == self.request.user.username:
                return self.request.user

        return super(UserViewSet, self).get_object()

    def list(self, request, *args, **kwargs):
        """
        Get users based on `search` query param.

        ###Response
        <pre><code>
        {
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
            "gender": 1,
            "image": "http://2ed106c1d72e039a6300-f673136b865c774b4127f2d581b9f607.r83.cf5.rackcdn.com/1NHUqCeh94NaWb8hlu74L7.jpg",
            "location": {
                "latitude": 25.1593957,
                "longitude": 55.2338326,
                "country": "AE",
                "postal_code": "857",
                "state": "Dubai",
                "city": "Dubai",
                "address": "Whatever Street 31",
                "google_geocode_response": {}  // when passed server will auto calculate the location attributes except latitude and longitude
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
        NOT IMPLEMENTED
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
        # user = self.get_object()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post', 'delete'], suffix='Listen', permission_classes=(IsAuthenticatedOrReadOnly,))
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
        ap = user.ap

        if request.user == user:
            raise ValidationError({'error': "You can not listen to your self"})

        if request.method == 'POST':
            listen_controller.listen_to_object(request.user, ap, request)
            msg = "you started listening to {} shouts.".format(user.name)
            _status = status.HTTP_201_CREATED
        else:
            listen_controller.stop_listening_to_object(request.user, ap)
            msg = "you stopped listening to {} shouts.".format(user.name)
            _status = status.HTTP_202_ACCEPTED
        ret = {
            'data': {'success': msg},
            'status': _status
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
        listeners = listen_controller.get_object_listeners(user.ap)
        page = self.paginate_queryset(listeners)
        serializer = UserSerializer(page, many=True, context={'request': request})
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
                - pages
                - tags
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """

        listening_type = request.query_params.get('type', 'users')
        if listening_type not in ['users', 'pages', 'tags']:
            raise ValidationError({'type': "should be `users`, `pages` or `tags`."})

        user = self.get_object()
        listening = getattr(user, 'listening2_' + listening_type)

        # we do not use the view pagination class since we need one with custom results field
        self.pagination_class = self.get_custom_shoutit_page_number_pagination_class(
            custom_results_field=listening_type)
        page = self.paginate_queryset(listening)

        result_object_serializers = {
            'users': UserSerializer,
            'pages': UserSerializer,
            'tags': TagSerializer,
        }
        result_object_serializer = result_object_serializers[listening_type]
        serializer = result_object_serializer(page, many=True, context={'request': request})

        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Home', permission_classes=(IsAuthenticated, IsOwner))
    def home(self, request, *args, **kwargs):
        """
        Get user homepage shouts

        User can't see the homepage of other users

        [Shouts Pagination](https://docs.google.com/document/d/1Zp9Ks3OwBQbgaDRqaULfMDHB-eg9as6_wHyvrAWa8u0/edit#heading=h.97r3lxfv95pj)
        ---
        serializer: ShoutSerializer
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
        self.pagination_class = PageNumberIndexPagination
        self.filter_backends = (HomeFilterBackend,)
        setattr(self, 'model', Shout)
        setattr(self, 'filters', {'is_disabled': False})
        setattr(self, 'select_related', ('item', 'category__main_tag', 'item__currency', 'user__profile'))
        setattr(self, 'prefetch_related', ('item__videos',))
        setattr(self, 'defer', ())
        shouts = self.filter_queryset(ShoutIndex.search())
        page = self.paginate_queryset(shouts)
        serializer = ShoutSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Shouts')
    def shouts(self, request, *args, **kwargs):
        """
        Get user shouts

        [Shouts Pagination](https://docs.google.com/document/d/1Zp9Ks3OwBQbgaDRqaULfMDHB-eg9as6_wHyvrAWa8u0/edit#heading=h.97r3lxfv95pj)
        ---
        serializer: ShoutSerializer
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
            - name: page_size
              paramType: query
        """
        user = self.get_object()

        shout_type = request.query_params.get('shout_type', 'all')
        if shout_type not in ['offer', 'request', 'all']:
            raise ValidationError({'shout_type': "should be `offer`, `request` or `all`."})

        # todo: refactor to use shout index filter
        self.pagination_class = PageNumberIndexPagination
        setattr(self, 'model', Shout)
        setattr(self, 'filters', {'is_disabled': False})
        setattr(self, 'select_related', ('item', 'category__main_tag', 'item__currency', 'user__profile'))
        setattr(self, 'prefetch_related', ('item__videos',))
        setattr(self, 'defer', ())
        shouts = ShoutIndex.search().filter('term', uid=user.pk).sort('-date_published')
        if shout_type != 'all':
            shouts = shouts.query('match', type=shout_type)

        page = self.paginate_queryset(shouts)
        serializer = ShoutSerializer(page, many=True, context={'request': request})
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
                },
                {
                    "images": [], // list of image urls
                    "videos": [], // list of {Video Object}s
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
        # Todo: move validation to the serializer
        user = self.get_object()
        logged_user = request.user
        if logged_user == user:
            raise ValidationError({'error': "You can not start a conversation with your self"})
        if not (message_controller.conversation_exist(users=[user, logged_user]) or user.is_listening(logged_user)):
            raise ValidationError({'error': "You can only start a conversation with your listeners"})
        context = {
            'request': request,
            'conversation': None,
            'to_users': [user]
        }
        serializer = MessageSerializer(data=request.data, partial=False, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_message_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_success_message_headers(self, data):
        loc = reverse('conversation-messages', kwargs={'id': data['conversation_id']}, request=self.request)
        return {'Location': loc}

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
        account = request.data.get('account') or request.query_params.get('account')
        if not account:
            raise ValidationError({'account': "This field is required."})
        if account not in ['facebook', 'gplus']:
            raise ValidationError({'account': "Unsupported account."})

        if request.method == 'PUT':
            if account == 'gplus':
                gplus_code = request.data.get('gplus_code')
                if not gplus_code:
                    raise ValidationError({'gplus_code': "please provide valid google plus code"})
                client = hasattr(request.auth, 'client') and request.auth.client.name or None
                gplus_controller.link_gplus_account(user, gplus_code, client)

            if account == 'facebook':
                facebook_access_token = request.data.get('facebook_access_token')
                if not facebook_access_token:
                    raise ValidationError({'facebook_access_token': "please provide valid facebook access token"})
                facebook_controller.link_facebook_account(user, facebook_access_token)

            msg = "{} linked successfully.".format(account.capitalize())

        else:
            if account == 'gplus':
                gplus_controller.unlink_gplus_user(user)

            if account == 'facebook':
                facebook_controller.unlink_facebook_user(user)

            msg = "{} unlinked successfully.".format(account.capitalize())

        ret = {
            'data': {'success': msg},
            'status': status.HTTP_202_ACCEPTED
        }

        return Response(**ret)
