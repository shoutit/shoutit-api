# -*- coding: utf-8 -*-
"""

"""
from django.utils.translation import ugettext_lazy as _
from rest_framework import viewsets, filters, status, mixins
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework_extensions.mixins import DetailSerializerMixin

from common.constants import USER_TYPE_PAGE
from shoutit.api.permissions import IsOwnerModify, IsOwner
from shoutit.api.v3.exceptions import ShoutitBadRequest
from shoutit.api.v3.views.shout_views import ShoutViewSet
from shoutit.controllers import listen_controller, message_controller
from shoutit.models import User
from ..filters import HomeFilterBackend, ProfileFilter
from ..pagination import ShoutitPageNumberPaginationNoCount, ShoutitPageNumberPagination
from ..serializers import (ProfileSerializer, ProfileDetailSerializer, MessageSerializer, TagDetailSerializer,
                           ProfileDeactivationSerializer, GuestSerializer, ProfileLinkSerializer,
                           ProfileContactsSerializer, ShoutSerializer, PageDetailSerializer, FacebookPageLinkSerializer)


class ProfileViewSet(DetailSerializerMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Profile API Resource.
    """
    lookup_field = 'username'
    lookup_value_regex = '[0-9a-zA-Z._]+'
    serializer_class = ProfileSerializer
    serializer_detail_class = ProfileDetailSerializer
    queryset = User.objects.filter(is_active=True, is_activated=True).select_related('profile', 'page')
    queryset_detail = User.objects.filter(is_active=True).select_related('profile', 'page', 'linked_facebook',
                                                                         'linked_gplus')
    pagination_class = ShoutitPageNumberPaginationNoCount
    filter_backends = (ProfileFilter, filters.SearchFilter)
    search_fields = ('=id', '=email', 'username', 'first_name', 'last_name')
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerModify)

    def get_object(self):
        username = self.kwargs.get(self.lookup_field)
        if self.request.user.is_authenticated():
            if username == 'me' or username == self.request.user.username:
                return self.request.user
        return super(ProfileViewSet, self).get_object()

    def get_serializer(self, *args, **kwargs):
        if args:
            instance = args[0]
            if isinstance(instance, User) and instance.is_guest:
                self.serializer_class = GuestSerializer
                self.serializer_detail_class = GuestSerializer
        return super(ProfileViewSet, self).get_serializer(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        List Profiles based on `search` and `country` query params.

        ####These attributes are omitted
        `location.latitude`, `location.longitude`, `location.address`

        ###Response
        <pre><code>
        {
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {ProfileSerializer}
        }
        </code></pre>
        ---
        serializer: ProfileSerializer
        parameters:
            - name: search
              paramType: query
            - name: country
              paramType: query
        """
        return super(ProfileViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a Profile

        ####These attributes will only show for Profile owner
        `email`, `mobile`, `gender`, `birthday`, `location.latitude`, `location.longitude`, `location.address`, `push_tokens`, `linked_accounts`, `stats`

        ####These attributes will not show for profile owner
        `is_listening`, `is_listener`, `conversation`

        ####This attribute will only show when it is possible to *start* chat with the profile
        `chat_url`
        ---
        serializer: ProfileDetailSerializer
        parameters:
            - name: username
              description: me for logged in profile
              paramType: path
              required: true
              defaultValue: me
        """
        instance = self.get_object()
        if instance.type == USER_TYPE_PAGE:
            self.serializer_detail_class = PageDetailSerializer
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Modify a Profile
        ###REQUIRES AUTH
        ###Request
        Specify any or all of these attributes to change them.
        ####Body
        <pre><code>
        {
            "username": "mo",
            "email": "mo.chawich@gmail.com",
            "mobile": "01501578444",
            "website": "https://www.shoutit.com",
            "first_name": "Mo",
            "last_name": "Chawich",
            "bio": "I'm a good shouter",
            "gender": "male",
            "image": "https://user-image.static.shoutit.com/user_uuid-timestamp.jpg",
            "cover": "https://user-image.static.shoutit.com/user_uuid-timestamp.jpg",
            "location": {
                "latitude": 25.1593957,
                "longitude": 55.2338326,
                "address": "Whatever Street 31"
            },
            "video": {
                "url": "https://shout-image.static.shoutit.com/38CB868F-B0C8-4B41-AF5A-F57C9FC666C7-1447616915.mp4",
                "thumbnail_url": "https://shout-image.static.shoutit.com/38CB868F-B0C8-4B41-AF5A-F57C9FC666C7-1447616915_thumbnail.jpg",
                "provider": "shoutit_s3",
                "id_on_provider": "38CB868F-B0C8-4B41-AF5A-F57C9FC666C7-1447616915",
                "duration": 12
            },
            "push_tokens": {
                "apns": "56yhnjflsdjfirjeoifjsorj4o",
                "gcm": "asjkdhsakjdhi3uhekndkjadkjsak"
            }
        }
        </code></pre>

        For `location` it is enough to pass `latitude` and `longitude` and the other location attributes such as:
        `country`, `state`, `city`, `postal_code` and `address` will be automatically filled by the API. Passing `address`
        will override the auto-filled one by server. `address` can be also sent alone, this way only saved address will be replaced not other attributes.

        ###Deleting video and/or push_tokens
        Set them as `null`
        ####Body
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
        serializer: ProfileDetailSerializer
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in profile
              paramType: path
              required: true
              defaultValue: me
            - name: body
              paramType: body
        """
        instance = self.get_object()
        if instance.type == USER_TYPE_PAGE:
            self.serializer_detail_class = PageDetailSerializer
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a Profile and everything attached to it
        ###REQUIRES AUTH
        ```
        NOT IMPLEMENTED AND ONLY USED FOR TEST USERS
        ```
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in profile
              paramType: path
              required: true
              defaultValue: me
        """
        user = self.get_object()
        if user.is_test:
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

    @detail_route(methods=['post', 'delete'], permission_classes=(IsAuthenticatedOrReadOnly,), suffix='Listen')
    def listen(self, request, *args, **kwargs):
        """
        Start/Stop listening to a Profile
        ###REQUIRES AUTH
        ###Start listening
        <pre><code>
        POST: /users/{username}/listen
        </code></pre>

        ###Stop listening
        <pre><code>
        DELETE: /users/{username}/listen
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        user = self.get_object()
        ap = user.ap
        api_client = getattr(request, 'api_client', None)

        if request.user == user:
            raise ShoutitBadRequest(_("You can't listen to your self"))

        if request.method == 'POST':
            listen_controller.listen_to_object(request.user, ap, api_client=api_client, api_version=request.version)
            msg = _("You started listening to shouts from %(name)s") % {'name': user.name}
        else:
            listen_controller.stop_listening_to_object(request.user, ap)
            msg = _("You stopped listening to shouts from %(name)s") % {'name': user.name}

        data = {
            'success': msg,
            'new_listeners_count': user.listeners_count
        }
        return Response(data=data, status=status.HTTP_202_ACCEPTED)

    @detail_route(methods=['get'], suffix='Listeners')
    def listeners(self, request, *args, **kwargs):
        """
        List the Profiles listening to this Profile
        Returned list is mix of Users and Pages
        ###Response
        <pre><code>
        {
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {ProfileSerializer}
        }
        </code></pre>
        ---
        serializer: ProfileSerializer
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in profile
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
        serializer = ProfileSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Listening')
    def listening(self, request, *args, **kwargs):
        """
        List the Profiles this Profile is listening to
        Returned list is a mix of Users and Pages
        ###Response
        <pre><code>
        {
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {ProfileSerializer}
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in profile
              paramType: path
              required: true
              defaultValue: me
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        user = self.get_object()
        listening = user.listening2_profiles
        page = self.paginate_queryset(listening)
        serializer = ProfileSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], suffix='Interests')
    def interests(self, request, *args, **kwargs):
        """
        List the Interests this Profile is listening to
        ###Response
        <pre><code>
        {
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {TagDetailSerializer}
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in profile
              paramType: path
              required: true
              defaultValue: me
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        user = self.get_object()
        listening = user.listening2_tags
        page = self.paginate_queryset(listening)
        serializer = TagDetailSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], permission_classes=(IsAuthenticated, IsOwner), suffix='Home')
    def home(self, request, *args, **kwargs):
        """
        List the Profile homepage shouts. Profile can't see the homepage of other profiles.
        [Shouts Pagination](https://github.com/shoutit/shoutit-api/wiki/Searching-Shouts#pagination)
        ###REQUIRES AUTH
        ###Response
        <pre><code>
        {
          "count": 0, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {ShoutSerializer}
        }
        </code></pre>
        ---
        omit_serializer: true
        parameters:
            - name: username
              description: me for logged in profile
              paramType: path
              required: true
              defaultValue: me
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        # Borrow `serializer_class`, `pagination_class` and `get_queryset` from ShoutViewSet
        self.get_object()  # to apply object permissions
        shout_view_set = ShoutViewSet()
        setattr(self, 'serializer_detail_class',
                shout_view_set.serializer_class)  # Using detail since this is a detail endpoint
        setattr(self, 'pagination_class', shout_view_set.pagination_class)
        setattr(self, 'get_queryset', shout_view_set.get_queryset)
        setattr(self, 'get_index_search', shout_view_set.get_index_search)
        setattr(self, 'filter_backends', [HomeFilterBackend])

        shouts = self.filter_queryset(self.get_index_search())
        page = self.paginate_queryset(shouts)
        serializer = self.get_serializer(page, many=True)
        result = self.get_paginated_response(serializer.data)
        return result

    @detail_route(methods=['post'], suffix='Message')
    def chat(self, request, *args, **kwargs):
        """
        Start or continue chatting (conversation whose its `type` is `chat`) with the Profile
        ###REQUIRES AUTH
        > Profile can only message its Listeners, or someone whom it already has an existing conversation with.
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
                    "profile": {
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
                    "videos": [] // list of {Video Object}s
                }
            ]
        }
        </code></pre>

        Either `text`, `attachments` or both has to be provided. Images and videos are to be compressed and uploaded before submitting. CDN urls should be sent.
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
            raise ShoutitBadRequest(_("You can not start a conversation with your self"))
        if not (message_controller.conversation_exist(users=[user, logged_user]) or user.is_listening(logged_user)):
            raise ShoutitBadRequest(_("You can only start a conversation with your listeners"))
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

    @detail_route(methods=['patch', 'delete'], suffix='Linked Accounts')
    def link(self, request, *args, **kwargs):
        """
        Link/Unlink external social accounts
        ###REQUIRES AUTH

        ###Link Facebook
        <pre><code>
        PATCH: /profiles/{username}/link
        {
            "account": "facebook",
            "facebook_access_token": "FACEBOOK_ACCESS_TOKEN"
        }
        </code></pre>

        ###Unlink Facebook
        <pre><code>
        DELETE: /profiles/{username}/link
        {
            "account": "facebook"
        }
        </code></pre>

        ###Link G+
        <pre><code>
        PATCH: /profiles/{username}/link
        {
            "account": "gplus",
            "gplus_code": "GOOGLE_GRANT_CODE"
        }
        </code></pre>

        ###Unlink G+
        <pre><code>
        DELETE: /profiles/{username}/link
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
        self.serializer_detail_class = ProfileLinkSerializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    @detail_route(methods=['post', 'delete'], suffix='Facebook Pages')
    def facebook_page(self, request, *args, **kwargs):
        """
        Link / unlink Facebook Page
        ###REQUIRES AUTH

        ###Link
        <pre><code>
        POST: /profiles/{username}/facebook_page
        {
            "facebook_page_id": "1234567890"
        }
        </code></pre>

        ###Unlink
        <pre><code>
        DELETE: /profiles/{username}/facebook_page
        {
            "facebook_page_id": "1234567890"
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
        self.serializer_detail_class = FacebookPageLinkSerializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    @detail_route(methods=['get'], suffix='Mutual Facebook Friends')
    def mutual_friends(self, request, *arg, **kwargs):
        """
        List this Profile's friends who are also on Shoutit
        Returned list is a mix of Users and Pages
        ###Response
        <pre><code>
        {
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {ProfileSerializer}
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in profile
              paramType: path
              required: true
              defaultValue: me
            - name: page
              paramType: query
            - name: page_size
              paramType: query
            """
        user = self.get_object()
        mutual_friends = user.mutual_friends
        page = self.paginate_queryset(mutual_friends)
        serializer = ProfileSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['patch'], suffix='Update Contacts')
    def contacts(self, request, *arg, **kwargs):
        """
        Upload Phone book Contacts of the logged in profile

        ###Body
        <pre><code>
        {
            "contacts": [
                {
                    "first_name": "John",
                    "last_name": "Doe",
                    "name": "",
                    "mobiles": ["+491501234567", "01501234567"],
                    "emails": ["john@example.com", "superman@andromeda.com"]
                },
                {
                    "first_name": "",
                    "last_name": "",
                    "name": "Sam Doe",
                    "mobiles": ["+96170364170"],
                    "emails": []
                }
            ]
        }
        </code></pre>

        - `first_name`, `last_name` and `name` are optional
        - `name` value is used only when `first_name` and `last_name` are empty, null or non existing
        - each string in `mobiles` should be either full mobile number with country code and `+` or valid mobile number from the country of the profile otherwise it will be skipped
        - each string in `emails` should be a valid email otherwise it will be skipped

        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in profile
              paramType: path
              required: true
              defaultValue: me
            """
        serializer = ProfileContactsSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response({'success': _("Your contacts have been uploaded")})

    @detail_route(methods=['get'], suffix='Mutual Contacts')
    def mutual_contacts(self, request, *arg, **kwargs):
        """
        List this Profile's contacts who are also on Shoutit
        Returned list is a mix of Users and Pages
        ###Response
        <pre><code>
        {
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {ProfileSerializer}
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in profile
              paramType: path
              required: true
              defaultValue: me
            - name: page
              paramType: query
            - name: page_size
              paramType: query
            """
        user = self.get_object()
        mutual_contacts = user.mutual_contacts
        page = self.paginate_queryset(mutual_contacts)
        serializer = ProfileSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['post'], permission_classes=(IsAuthenticated, IsOwner), suffix="Deactivate user's account")
    def deactivate(self, request, *args, **kwargs):
        """
        Deactivate profile
        ###REQUIRES AUTH, Account owner

        ####Body
        <pre><code>
        {
            "password": "current password"
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        user = self.get_object()
        serializer = ProfileDeactivationSerializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['get'], suffix='Profile Pages')
    def pages(self, request, *args, **kwargs):
        """
        List the Profile pages
        Returned list is profiles of type `page`
        ###Response
        <pre><code>
        {
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {ProfileSerializer}
        }
        </code></pre>
        ---
        serializer: ProfileSerializer
        omit_parameters:
            - form
        parameters:
            - name: username
              description: me for logged in profile
              paramType: path
              required: true
              defaultValue: me
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        self.serializer_detail_class = ProfileSerializer
        user = self.get_object()
        pages = user.pages.all()
        page = self.paginate_queryset(pages)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @detail_route(methods=['get'], permission_classes=(IsAuthenticated, IsOwner), suffix='Bookmarks')
    def bookmarks(self, request, *args, **kwargs):
        """
        List the Profile bookmarked shouts. Profile can't see the bookmarks of other profiles.
        [Shouts Pagination](https://github.com/shoutit/shoutit-api/wiki/Searching-Shouts#pagination)
        ###REQUIRES AUTH
        ###Response
        <pre><code>
        {
          "count": 0, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {ShoutSerializer}
        }
        </code></pre>
        ---
        omit_serializer: true
        parameters:
            - name: username
              description: me for logged in profile
              paramType: path
              required: true
              defaultValue: me
            - name: page
              paramType: query
            - name: page_size
              paramType: query
        """
        user = self.get_object()
        self.serializer_detail_class = ShoutSerializer
        self.pagination_class = ShoutitPageNumberPagination
        shouts = self.filter_queryset(user.bookmarks.get_valid_shouts().order_by('-bookmarks__created_at'))
        page = self.paginate_queryset(shouts)
        serializer = self.get_serializer(page, many=True)
        result = self.get_paginated_response(serializer.data)
        return result
