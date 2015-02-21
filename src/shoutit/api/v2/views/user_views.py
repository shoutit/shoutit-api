# -*- coding: utf-8 -*-
"""

"""
from __future__ import unicode_literals

from rest_framework import permissions, viewsets, filters, mixins, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from rest_framework_extensions.mixins import DetailSerializerMixin

from shoutit.controllers import user_controller, stream_controller

from shoutit.models import User
from shoutit.api.v2.serializers import UserSerializer, UserDetailSerializer, TagSerializer
from shoutit.api.v2.permissions import IsOwnerOrReadOnly


class _UserViewSet(viewsets.ModelViewSet):
    lookup_field = 'username'
    lookup_value_regex = '[0-9a-zA-Z.]{2,30}'
    serializer_class = UserSerializer

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('id', 'username', 'email')
    search_fields = ('username', 'first_name', 'last_name', '=email')

    def get_queryset(self):
        return User.objects.all()


class UserViewSet(DetailSerializerMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """
    User API Resource.

    """
    lookup_field = 'username'
    lookup_value_regex = '[0-9a-zA-Z.]{2,30}'

    serializer_class = UserSerializer
    serializer_detail_class = UserDetailSerializer

    queryset = User.objects.all()
    queryset_detail = queryset.prefetch_related('profile')

    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    filter_fields = ('id', 'username', 'email')
    search_fields = ('username', 'first_name', 'last_name', '=email')

    def get_custom_pagination_serializer(self, page, serializer_class):
        """
        Return a serializer instance to use with paginated data using the `serializer_class` param
        """
        class SerializerClass(self.pagination_serializer_class):
            class Meta:
                object_serializer_class = serializer_class

        pagination_serializer_class = SerializerClass
        context = self.get_serializer_context()
        return pagination_serializer_class(instance=page, context=context)

    def list(self, request, *args, **kwargs):
        """
        Get users based on `search` query param.

        ###User Object
        <pre><code>
        {
          "id": "a45c843f-8983-4f55-bde4-0236f070151d",
          "api_url": "http://shoutit.dev:8000/api/v2/users/syron",
          "username": "syron",
          "name": "Mo Chawich",
          "first_name": "Mo",
          "last_name": "Chawich",
          "web_url": "",
          "is_active": true
        }
        </code></pre>

        ###Response
        <pre><code>
        {
          "count": 7, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {User Object} as described above
        }
        </code></pre>

        ---
        omit_serializer: true
        parameters:
            - name: search
              paramType: query
        """
        instance = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(instance)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(instance, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Get user

        ###Response {User detailed object}
        <pre><code>
        {
          "id": "65682def-d120-40f4-92b8-4d99361bdc6d",
          "api_url": "http://shoutit.dev:8000/api/v2/users/mo",
          "username": "mo",
          "name": "Mohamad Nour Chawich",
          "first_name": "Mohamad Nour",
          "last_name": "Chawich",
          "web_url": "",
          "is_active": true,
          "image": "http://2ed106c1d72e039a6300-f673136b865c774b4127f2d581b9f607.r83.cf5.rackcdn.com/1NHUqCeh94NaWb8hlu74L7.jpg",
          "sex": true,
          "video": null,
          "date_joined": 1424292476,
          "bio": "Shoutit Master 2!",
          "location": {
            "latitude": 25.1593957,
            "country": "AE",
            "longitude": 55.2338326,
            "city": "Dubai"
          },
          "email": "mo.chawich@gmail.com",
          "social_channels": {
            "gplus": false,
            "facebook": true
          },
          "push_tokens": {
            "apns": "56yhnjflsdjfirjeoifjsorj4o",
            "gcm": "asjkdhsakjdhi3uhekndkjadkjsak"
          }
        }
        </code></pre>

        ---
        omit_serializer: true
        parameters:
            - name: username
              paramType: path
              required: true
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Modify user

        ###Request
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
        <code><pre>
        {
            "video": null,
            "push_tokens": {
                "apns": null,
                "gcm": null
            }
        }
        </code></pre>

        ###Response
        Detailed User object
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters_strategy:
            form: replace
            query: merge

        parameters:
            - name: body
              paramType: body
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # def destroy(self, request, *args, **kwargs):
    #     """
    #     Delete user and everything attached to him
    #
    #     ###Request
    #     <pre><code>
    #     </code></pre>
    #
    #     ---
    #     responseMessages:
    #         - code: 204
    #           message: User Deleted
    #     omit_serializer: true
    #     omit_parameters:
    #         - form
    #     parameters:
    #         - name: body
    #           paramType: body
    #     """
    #     return super(UserViewSet, self).destroy(request, *args, **kwargs)

    @detail_route(methods=['put'])
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
        ###Response
        Detailed User object
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: image_file
              type: file
        """
        return self.partial_update(request, *args, **kwargs)

    @detail_route(methods=['post', 'delete'])
    def listen(self, request, *args, **kwargs):
        """
        Start/Stop listening to user

        ###Listen
        <pre><code>
        POST: /api/v2/users/{username}/listen
        </code></pre>

        ###Stop listening
        <pre><code>
        DELETE: /api/v2/users/{username}/listen
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        """
        user = self.get_object()
        profile = user.profile

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

    @detail_route(methods=['get'])
    def listeners(self, request, *args, **kwargs):
        """
        Get user listeners

        ###Response
        <pre><code>
        {
          "count": 4, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {User Object} as described above
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: page
              paramType: query
        """
        user = self.get_object()
        listeners = stream_controller.get_stream_listeners(user.profile.stream2)
        page = self.paginate_queryset(listeners)
        if page is not None:
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(listeners, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def listening(self, request, *args, **kwargs):
        """
        Get user listening

        ###Tag Object
        <pre><code>
        {
          "id": "a45c843f-8473-2135-bde4-0236754f151d",
          "name": "computer-games",
          "api_url": "http://shoutit.dev:8000/api/v2/tags/computer-games",
          "web_url": "http://shoutit.dev:8000/tag/computer-games",
          "is_listening": true,
          "listeners_count": 321
        }
        </code></pre>

        ###Response
        <pre><code>
        {
          "count": 4, // number of results
          "next": null, // next results page url
          "previous": null, // previous results page url
          "results": [] // list of {User Object} or {Tags Object} as described above
        }
        </code></pre>
        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: listening_type
              description:
              paramType: query
              required: true
              defaultValue: users
              enum:
                - users
                - tags
            - name: page
              paramType: query

        """

        listening_type = request.query_params.get('listening_type', 'users')
        if listening_type not in ['users', 'tags']:
            raise ValidationError({'listening_type': "should be `users` or `tags`."})

        user = self.get_object()

        listening = stream_controller.get_user_listening_qs(user, listening_type)
        page = self.paginate_queryset(listening)

        if listening_type == 'users':
            if page is not None:
                serializer = self.get_custom_pagination_serializer(page, UserSerializer)
            else:
                serializer = self.get_serializer(listening, many=True)
            return Response(serializer.data)

        if listening_type == 'tags':
            if page is not None:
                serializer = self.get_custom_pagination_serializer(page, TagSerializer)
            else:
                serializer = self.get_serializer(listening, many=True)
            return Response(serializer.data)


    @detail_route(methods=['get'])
    def shouts(self, request, *args, **kwargs):
        """
        Get user shouts

        ###Response
        <pre><code>
        </code></pre>

        ---
        omit_serializer: true
        omit_parameters:
            - form
        parameters:
            - name: type
              paramType: query
              required: true
              defaultValue: offers
              enum:
                - requests
                - offers
            - name: page
              paramType: query
        """
        return Response()
