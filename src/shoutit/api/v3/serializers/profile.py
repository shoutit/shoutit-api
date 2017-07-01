"""

"""
from collections import OrderedDict

from django.contrib.auth.models import AnonymousUser
from django.core.validators import URLValidator, validate_email
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, exceptions as drf_exceptions
from rest_framework.fields import empty
from rest_framework.request import clone_request
from rest_framework.reverse import reverse

from common.constants import USER_TYPE_PAGE
from shoutit.api.serializers import AttachedUUIDObjectMixin, HasAttachedUUIDObjects
from shoutit.api.v3 import exceptions
from shoutit.api.v3.exceptions import RequiredBody, ShoutitBadRequest
from shoutit.controllers import (message_controller, location_controller, notifications_controller, facebook_controller,
                                 gplus_controller, mixpanel_controller)
from shoutit.models import User, InactiveUser, Profile, Page, Video, ProfileContact
from shoutit.models.user import gender_choices
from shoutit.utils import url_with_querystring, correct_mobile, blank_to_none
from .base import VideoSerializer, LocationSerializer, PushTokensSerializer, empty_char_input


class MiniProfileSerializer(AttachedUUIDObjectMixin, serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'name')


class ProfileSerializer(MiniProfileSerializer):
    api_url = serializers.HyperlinkedIdentityField(view_name='profile-detail', lookup_field='username')
    type = serializers.CharField(source='v3_type_name', help_text="'user' or 'page'", read_only=True)
    image = serializers.URLField(source='ap.image', **empty_char_input)
    cover = serializers.URLField(source='ap.cover', **empty_char_input)
    is_listening = serializers.SerializerMethodField(help_text="Whether you are listening to this Profile")
    listeners_count = serializers.ReadOnlyField(help_text="Number of profiles (users, pages) Listening to this Profile")
    is_owner = serializers.SerializerMethodField(help_text="Whether this profile is yours")
    location = LocationSerializer(help_text="latitude and longitude are only shown for owner", required=False)

    class Meta(MiniProfileSerializer.Meta):
        parent_fields = MiniProfileSerializer.Meta.fields
        fields = parent_fields + ('type', 'api_url', 'web_url', 'app_url', 'first_name', 'last_name', 'is_activated',
                                  'image', 'cover', 'is_listening', 'listeners_count', 'is_owner', 'location')

    def __init__(self, instance=None, data=empty, **kwargs):
        super(ProfileSerializer, self).__init__(instance, data, **kwargs)
        self.fields['username'].required = False

    def get_is_listening(self, tag):
        request = self.root.context.get('request')
        user = request and request.user
        return user and user.is_authenticated() and user.is_listening(tag)

    # Todo (mo): Find what clients use `is_owner` for
    def get_is_owner(self, user):
        return user.is_owner(self.root.context['request'].user)

    def to_representation(self, instance):
        if not instance.is_active:
            ret = InactiveUser().to_dict
        else:
            ret = super(ProfileSerializer, self).to_representation(instance)
        # hide sensitive attributes from other users than owner
        if not ret['is_owner']:
            del ret['location']['latitude']
            del ret['location']['longitude']
            del ret['location']['address']
        blank_to_none(ret, ['image', 'cover'])
        if instance.type == USER_TYPE_PAGE and 'view' in self.context and self.context['view'].action == 'pages':
            user = self.context['request'].user
            if instance.page.is_admin(user):
                ret['stats'] = instance.stats
        return ret


# Todo: subclasses UserSerializer, UserDetailSerializer and PageSerializer
class ProfileDetailSerializer(ProfileSerializer):
    email = serializers.EmailField(allow_blank=True, max_length=254, required=False, help_text="Only shown for owner")
    mobile = serializers.CharField(source='profile.mobile', min_length=4, max_length=20, **empty_char_input)
    is_password_set = serializers.BooleanField(read_only=True)
    date_joined = serializers.IntegerField(source='created_at_unix', read_only=True)
    gender = serializers.ChoiceField(source='profile.gender', choices=gender_choices,
                                     help_text='male, female, other or `null`', **empty_char_input)
    birthday = serializers.DateField(source='profile.birthday', required=False, allow_null=True,
                                     help_text='Formatted as YYYY-MM-DD')
    bio = serializers.CharField(source='profile.bio', max_length=160, **empty_char_input)
    video = VideoSerializer(source='ap.video', required=False, allow_null=True)
    website = serializers.CharField(max_length=200, source='ap.website', **empty_char_input)
    push_tokens = PushTokensSerializer(help_text="Only shown for owner", required=False)
    linked_accounts = serializers.ReadOnlyField(help_text="only shown for owner")
    is_listener = serializers.SerializerMethodField(help_text="Whether this profile is listening you")
    listeners_url = serializers.SerializerMethodField(help_text="URL to get this profile listeners")
    listening_count = serializers.ReadOnlyField(
        help_text="Object specifying the number of profile listening. It has 'users', 'pages' and 'tags' properties")
    listening_url = serializers.SerializerMethodField(help_text="URL to get the Profiles this profile is listening to")
    interests_url = serializers.SerializerMethodField(help_text="URL to get the Interests of this profile")
    shouts_url = serializers.SerializerMethodField(help_text="URL to show shouts of this profile")
    conversation = serializers.SerializerMethodField(
        help_text="Conversation with type `chat` between you and this profile if exists")
    chat_url = serializers.SerializerMethodField(help_text="URL to message this profile if it is possible. This is the "
                                                           "case when the profile is one of your listeners or an "
                                                           "existing previous conversation")

    stats = serializers.ReadOnlyField(
        help_text="Object specifying `unread_conversations_count` and `unread_notifications_count`")
    admin = serializers.SerializerMethodField(help_text="DetailedProfile for the currently logged in page admin if any."
                                                        "This is only shown for Pages")

    # Deprecate in 3.1
    pages = serializers.SerializerMethodField()
    admins = serializers.SerializerMethodField()

    class Meta(ProfileSerializer.Meta):
        parent_fields = ProfileSerializer.Meta.fields
        fields = parent_fields + (
            'gender', 'birthday', 'video', 'date_joined', 'bio', 'email', 'mobile', 'website', 'linked_accounts',
            'push_tokens', 'is_password_set', 'is_listener', 'shouts_url', 'listeners_url', 'listening_count',
            'listening_url', 'interests_url', 'conversation', 'chat_url', 'stats', 'admin', 'pages', 'admins'
        )

    def get_is_listener(self, user):
        request = self.root.context.get('request')
        signed_user = request and request.user
        return signed_user and signed_user.is_authenticated() and user.is_listening(signed_user)

    def get_shouts_url(self, user):
        shouts_url = reverse('shout-list', request=self.context['request'])
        return url_with_querystring(shouts_url, user=user.username)

    def get_listening_url(self, user):
        return reverse('profile-listening', kwargs={'username': user.username}, request=self.context['request'])

    def get_interests_url(self, user):
        return reverse('profile-interests', kwargs={'username': user.username}, request=self.context['request'])

    def get_listeners_url(self, user):
        return reverse('profile-listeners', kwargs={'username': user.username}, request=self.context['request'])

    def get_chat_url(self, user):
        return reverse('profile-chat', kwargs={'username': user.username}, request=self.context['request'])

    def get_conversation(self, user):
        from .conversation import ConversationDetailSerializer
        request_user = self.root.context['request'].user
        if isinstance(request_user, AnonymousUser) or request_user.id == user.id:
            return None
        conversation = message_controller.conversation_exist(users=[request_user, user])
        if not conversation:
            return None
        return ConversationDetailSerializer(conversation, context=self.root.context).data

    def get_admin(self, user):
        request = self.root.context.get('request')
        page_admin_user = request and getattr(request, 'page_admin_user', None)
        if not page_admin_user:
            return None
        # Serializing the admin profile requires a request with its user set to him
        admin_request = clone_request(request, request.method)
        admin_request._user = page_admin_user
        context = {'request': admin_request}
        return ProfileDetailSerializer(instance=page_admin_user, context=context).data

    def get_admins(self, user):
        return []

    def get_pages(self, user):
        return []

    def to_representation(self, instance):
        if not instance.is_active:
            return InactiveUser().to_dict
        ret = super(ProfileDetailSerializer, self).to_representation(instance)

        # Compatibility hack for iOS v3 clients that still expect v2_linked_accounts
        self.ios_compat_la(ret)

        # hide sensitive attributes from other users than owner
        if not ret['is_owner']:
            del ret['email']
            del ret['mobile']
            del ret['gender']
            del ret['birthday']
            del ret['push_tokens']
            del ret['linked_accounts']
            del ret['stats']
            if not ret['is_listener']:
                del ret['chat_url']

        # hide obvious attributes if the user `is_owner`
        else:
            del ret['is_listening']
            del ret['is_listener']
            del ret['conversation']
            del ret['chat_url']

        if not ret['type'] == 'page':  # v3 profile type
            del ret['admin']

        blank_to_none(ret, ['image', 'cover', 'gender', 'video', 'bio', 'about', 'mobile', 'website'])
        return ret

    def ios_compat_la(self, ret):
        request = self.context['request']
        if request.agent == 'ios' and request.build_no < 1280:
            ret['linked_accounts'] = self.instance.v2_linked_accounts
        return ret

    def to_internal_value(self, data):
        validated_data = super(ProfileDetailSerializer, self).to_internal_value(data)

        # Force partial=false validation for video
        has_video = 'video' in data
        profile_data = validated_data.get('ap', {})
        video_data = profile_data.get('video', {})
        if has_video and isinstance(video_data, OrderedDict):
            vs = VideoSerializer(data=video_data)
            if not vs.is_valid():
                raise serializers.ValidationError({['video']: vs.errors})

        return validated_data

    def validate_email(self, email):
        user = self.context['request'].user
        email = email.lower()
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            raise serializers.ValidationError(_('This email is used by another account'))
        return email

    def validate_website(self, website):
        if website:
            website = website.lower()
            # If no URL scheme given, assume http://
            if '://' not in website:
                website = u'http://%s' % website
            URLValidator()(website)
        return website

    def validate_mobile(self, mobile):
        if mobile:
            user = self.context['request'].user
            mobile = correct_mobile(mobile, user.location['country'], raise_exception=True)
        return mobile

    def update(self, user, validated_data):
        request = self.context['request']
        page_admin_user = getattr(request, 'page_admin_user', None)
        user_update_fields = []
        ap = user.ap
        ap_update_fields = []

        # User
        # Username
        new_username = validated_data.get('username')
        if new_username and new_username != user.username:
            user.username = new_username
            user_update_fields.append('username')
        # First name
        new_first_name = validated_data.get('first_name')
        if new_first_name and new_first_name != user.first_name:
            user.first_name = new_first_name
            user_update_fields.append('first_name')
        # Last name
        new_last_name = validated_data.get('last_name')
        if new_last_name and new_last_name != user.last_name:
            user.last_name = new_last_name
            user_update_fields.append('last_name')
        # Email
        new_email = validated_data.get('email')
        if new_email and new_email != user.email:
            user.email = new_email
            user_update_fields.extend(['email', 'is_activated'])
        # Save
        user.notify = False
        user.save(update_fields=user_update_fields)

        # Location
        location_data = validated_data.get('location', {})
        if location_data:
            location_controller.update_profile_location(ap, location_data)

        # AP
        ap_data = validated_data.get('ap', {})
        profile_data = validated_data.get('profile', {})
        page_data = validated_data.get('page', {})

        def fill(obj, data, fields):
            for field in fields:
                if field in data:
                    setattr(obj, field, data[field])
                    ap_update_fields.append(field)

        if isinstance(ap, Profile):
            fill(ap, profile_data, ['bio', 'gender', 'mobile', 'birthday'])

        elif isinstance(ap, Page):
            fill(ap, page_data, ['is_published', 'about', 'description', 'phone', 'founded', 'impressum',
                                 'overview', 'mission', 'general_info'])
            if 'name' in validated_data:
                ap.name = validated_data['name']
                ap_update_fields.append('name')

        if ap_data:
            fill(ap, ap_data, ['image', 'cover', 'website'])

            video_data = ap_data.get('video', {})
            if video_data:
                video = Video.create(url=video_data['url'], thumbnail_url=video_data['thumbnail_url'],
                                     provider=video_data['provider'], id_on_provider=video_data['id_on_provider'],
                                     duration=video_data['duration'])
                ap.video = video
                ap_update_fields.append('video')

            # if video sent as null, delete existing video
            elif video_data is None and ap.video:
                # ap.video.delete()
                ap.video = None
                ap_update_fields.append('video')

        if ap_data or profile_data or page_data:
            ap.notify = False
            ap.save(update_fields=ap_update_fields)

        # Push Tokens
        push_tokens_data = validated_data.get('push_tokens', {})
        if push_tokens_data:
            # Pages shouldn't update their push token, only admins should.
            if page_admin_user:
                # Push Tokens (admin)
                page_admin_user.update_push_tokens(push_tokens_data, 'v3')
                # Notify about the push token update
                notifications_controller.notify_user_of_profile_update(page_admin_user)
                # Update Mixpanel People record with new push tokens
                mixpanel_controller.add_to_mp_people([page_admin_user.id])
            else:
                user.update_push_tokens(push_tokens_data, 'v3')

        # Notify about updates
        notifications_controller.notify_user_of_profile_update(user)

        # Update Mixpanel People record
        mixpanel_controller.add_to_mp_people([user.id])
        return user


class GuestSerializer(ProfileSerializer):
    location = LocationSerializer(help_text="latitude and longitude are only shown for owner", required=False)
    push_tokens = PushTokensSerializer(required=False)
    date_joined = serializers.IntegerField(source='created_at_unix', read_only=True)

    class Meta(ProfileSerializer.Meta):
        fields = ('id', 'type', 'api_url', 'username', 'is_guest', 'date_joined', 'location', 'push_tokens')

    def to_representation(self, instance):
        ret = super(ProfileSerializer, self).to_representation(instance)
        return ret

    def update(self, user, validated_data):
        ap = user.ap

        # Location
        location_data = validated_data.get('location', {})
        if location_data:
            location_controller.update_profile_location(ap, location_data)

        # Push Tokens
        push_tokens_data = validated_data.get('push_tokens', {})
        if push_tokens_data:
            user.update_push_tokens(push_tokens_data, 'v3')

        # Update Mixpanel People record
        mixpanel_controller.add_to_mp_people([user.id])

        return user


class ProfileLinkSerializer(serializers.Serializer):
    account = serializers.ChoiceField(choices=['facebook', 'gplus'])
    facebook_access_token = serializers.CharField(required=False)
    gplus_code = serializers.CharField(required=False)

    def to_internal_value(self, data):
        validated_data = super(ProfileLinkSerializer, self).to_internal_value(data)
        request = self.context['request']
        user = request.user
        action = None
        account = validated_data['account']
        account_name = _("Facebook") if account == 'facebook' else _("Google") if account == 'gplus' else ''
        could_not_link = _("Couldn't link your %(account)s account") % {'account': account_name}
        could_not_unlink = _("Couldn't unlink your %(account)s account. You must set your password first.") % {'account': account_name}

        if request.method == 'PATCH':
            action = _('linked')
            if account == 'gplus':
                gplus_code = validated_data.get('gplus_code')
                if not gplus_code:
                    raise RequiredBody('gplus_code', message=could_not_link,
                                       developer_message="Provide a valid `gplus_code`")
                client = request.auth.client.name if hasattr(request.auth, 'client') else 'shoutit-test'
                gplus_controller.link_gplus_account(user, gplus_code, client)

            elif account == 'facebook':
                facebook_access_token = validated_data.get('facebook_access_token')
                if not facebook_access_token:
                    raise RequiredBody('facebook_access_token', message=could_not_link,
                                       developer_message="Provide a valid `facebook_access_token`")
                facebook_controller.link_facebook_account(user, facebook_access_token)

        elif request.method == 'DELETE':
            action = _('unlinked')
            if account == 'gplus':
                if not user.is_password_set and not getattr(user, 'linked_facebook', None):
                    raise ShoutitBadRequest(could_not_unlink)
                gplus_controller.unlink_gplus_user(user)
            elif account == 'facebook':
                if not user.is_password_set and not getattr(user, 'linked_gplus', None):
                    raise ShoutitBadRequest(could_not_unlink)
                facebook_controller.unlink_facebook_user(user)

        if action:
            success = _("Your %(account)s account has been %(action)s") % {'account': account_name, 'action': action}
            res = {'success': success}
            # Send `profile_update` on Pusher
            notifications_controller.notify_user_of_profile_update(user)
        else:
            res = {'success': _("No changes were made")}
        return res

    def to_representation(self, instance):
        return self.validated_data


class FacebookPageLinkSerializer(serializers.Serializer):
    facebook_page_id = serializers.CharField()

    def to_internal_value(self, data):
        validated_data = super(FacebookPageLinkSerializer, self).to_internal_value(data)
        request = self.context['request']
        user = request.user
        action = None
        linked_facebook = getattr(user, 'linked_facebook', None)
        if not linked_facebook:
            raise ShoutitBadRequest(_('You must link your Facebook account first'))
        facebook_page_id = validated_data['facebook_page_id']

        could_not_link = _("Couldn't link your Facebook Page")
        could_not_unlink = _("Couldn't unlink your Facebook Page")

        if request.method == 'POST':
            action = _('linked')
            try:
                facebook_controller.link_facebook_page(linked_facebook, facebook_page_id)
            except Exception as e:
                raise ShoutitBadRequest(could_not_link, developer_message=e)

        elif request.method == 'DELETE':
            action = _('unlinked')
            try:
                facebook_controller.unlink_facebook_page(linked_facebook, facebook_page_id)
            except Exception as e:
                raise ShoutitBadRequest(could_not_unlink, developer_message=e)

        if action:
            success = _("Your Facebook Page has been %(action)s") % {'action': action}
            res = {'success': success}
            # Send `profile_update` on Pusher
            notifications_controller.notify_user_of_profile_update(user)
        else:
            res = {'success': _("No changes were made")}
        return res

    def to_representation(self, instance):
        return self.validated_data


class ProfileContactSerializer(serializers.Serializer):
    first_name = serializers.CharField(**empty_char_input)
    last_name = serializers.CharField(**empty_char_input)
    name = serializers.CharField(**empty_char_input)
    emails = serializers.ListSerializer(child=serializers.CharField(**empty_char_input), allow_empty=True)
    mobiles = serializers.ListSerializer(child=serializers.CharField(**empty_char_input), allow_empty=True)

    def to_internal_value(self, data):
        ret = super(ProfileContactSerializer, self).to_internal_value(data)
        first_name = ret.get('first_name', '')
        last_name = ret.get('last_name', '')

        if not first_name or not last_name:
            name = ret.get('name', '')
            names = name.split()
            if len(names) >= 2:
                first_name = " ".join(names[0:-1])
                last_name = names[-1]
            elif len(names) == 1:
                first_name = names[0]
                last_name = ''
        ret['first_name'] = first_name[:30]
        ret['last_name'] = last_name[:30]
        return ret

    def validate_emails(self, emails):
        def _email(e):
            try:
                e = e.lower().replace(' ', '')
                validate_email(e)
                return e
            except:
                return None

        emails = map(_email, emails)
        emails = [email for email in emails if email]
        return emails

    def validate_mobiles(self, mobiles):
        request = self.root.context['request']
        user = request.user
        country = user.ap.country

        def _mobile(m):
            try:
                m = "".join(i for i in m if ord(i) < 128)
                m = m.replace(' ', '')
                if m.startswith('+'):
                    return m
                return correct_mobile(mobile=m, country=country)
            except:
                return None

        mobiles = map(_mobile, mobiles)
        mobiles = [mobile for mobile in mobiles if mobile]
        return mobiles


class ProfileContactsSerializer(serializers.Serializer):
    contacts = ProfileContactSerializer(many=True)

    def to_internal_value(self, data):
        ret = super(ProfileContactsSerializer, self).to_internal_value(data)
        request = self.context['request']
        user = request.user
        contacts = ret.get('contacts')

        def profile_contact(c):
            first_name = c['first_name']
            last_name = c['last_name']
            emails = c['emails']
            mobiles = c['mobiles']
            return ProfileContact(user=user, first_name=first_name, emails=emails, last_name=last_name, mobiles=mobiles)

        user.contacts.all().delete()
        profile_contacts = map(profile_contact, contacts)
        profile_contacts = [pc for pc in profile_contacts if pc.is_reached()]
        ProfileContact.objects.bulk_create(profile_contacts)
        return ret


class ObjectProfileActionSerializer(HasAttachedUUIDObjects, serializers.Serializer):
    """
    Should be initialized in the view
    ```
    instance = self.get_object()
    serializer = self.get_serializer(instance, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    ```

    Object must have `is_admin(user)`

    Subclasses must
    - Define these attributes that contain `%(name)s`
    `success_message`, `error_message`
    - Implement these methods
    `condition(self, instance, actor, profile)`, `create(self, validated_data)`
    """
    profile = ProfileSerializer()

    def to_internal_value(self, data):
        instance = self.instance
        request = self.context['request']
        actor = request.user
        page_admin_user = getattr(request, 'page_admin_user', None)
        if not instance.is_admin(actor):
            raise drf_exceptions.PermissionDenied()

        validated_data = super(ObjectProfileActionSerializer, self).to_internal_value(data)
        profile = self.fields['profile'].instance

        if actor == profile or page_admin_user == profile:
            raise exceptions.ShoutitBadRequest(_("You can't make actions against your own profile"),
                                               reason=exceptions.ERROR_REASON.BAD_REQUEST)
        if not self.condition(instance, actor, profile):
            raise exceptions.InvalidBody('profile', self.error_message % {'name': profile.name})

        return validated_data

    def to_representation(self, instance):
        profile = self.fields['profile'].instance
        return {'success': self.success_message % {'name': profile.name}}

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')
