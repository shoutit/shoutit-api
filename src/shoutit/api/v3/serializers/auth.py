"""

"""
from __future__ import unicode_literals

import random

from django.contrib.auth import login
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from ipware.ip import get_real_ip
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from common.constants import TOKEN_TYPE_RESET_PASSWORD
from shoutit.controllers import (facebook_controller, gplus_controller, user_controller, location_controller,
                                 page_controller)
from shoutit.models import User, DBCLConversation, ConfirmToken
from .page import PageCategorySerializer
from .profile import ProfileDetailSerializer, GuestSerializer


# Todo: change `user` to `profile` in all serializers
class FacebookAuthSerializer(serializers.Serializer):
    facebook_access_token = serializers.CharField(max_length=512)
    user = ProfileDetailSerializer(required=False)
    profile = ProfileDetailSerializer(required=False)

    def to_internal_value(self, data):
        ret = super(FacebookAuthSerializer, self).to_internal_value(data)
        request = self.context.get('request')
        facebook_access_token = ret.get('facebook_access_token')
        initial_profile = ret.get('profile') or ret.get('user')
        user = facebook_controller.user_from_facebook_auth_response(facebook_access_token, initial_profile,
                                                                    request.is_test)
        self.instance = user
        return ret


class GplusAuthSerializer(serializers.Serializer):
    gplus_code = serializers.CharField(max_length=4096)
    user = ProfileDetailSerializer(required=False)
    profile = ProfileDetailSerializer(required=False)

    def to_internal_value(self, data):
        ret = super(GplusAuthSerializer, self).to_internal_value(data)
        request = self.context.get('request')
        gplus_code = ret.get('gplus_code')
        # Todo (mo) apply Facebook logic for initial_profile
        initial_profile = ret.get('profile', {}) or ret.get('user', {})
        initial_profile['ip'] = get_real_ip(request)
        user = gplus_controller.user_from_gplus_code(gplus_code, initial_profile, request.client, request.is_test)
        self.instance = user
        return ret


class ShoutitSignupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=70)
    first_name = serializers.CharField(min_length=2, max_length=30, required=False)
    last_name = serializers.CharField(min_length=1, max_length=30, required=False)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, max_length=30)
    user = ProfileDetailSerializer(required=False)
    profile = ProfileDetailSerializer(required=False)

    def to_internal_value(self, data):
        if not data:
            data = {}
        name = data.get('name', 'user')
        names = name.split()
        if len(names) >= 2:
            data['first_name'] = " ".join(names[0:-1])
            data['last_name'] = names[-1]
        elif len(names) >= 1:
            data['first_name'] = names[0]
            data['last_name'] = random.randint(0, 999)
        else:
            data['first_name'] = 'user'
            data['last_name'] = random.randint(0, 999)

        ret = super(ShoutitSignupSerializer, self).to_internal_value(data)
        return ret

    def validate_email(self, email):
        email = email.lower()
        if User.exists(email=email):
            raise serializers.ValidationError(_('This email is used by another account'))
        return email

    def create(self, validated_data):
        request = self.context.get('request')
        initial_profile = validated_data.get('profile', {}) or validated_data.get('user', {})
        initial_profile['ip'] = get_real_ip(request)
        user = user_controller.user_from_shoutit_signup_data(validated_data, initial_profile, request.is_test)
        return user


class ShoutitLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()
    user = ProfileDetailSerializer(required=False)
    profile = ProfileDetailSerializer(required=False)

    def to_internal_value(self, data):
        ret = super(ShoutitLoginSerializer, self).to_internal_value(data)
        email = ret.get('email').lower()
        password = ret.get('password')
        initial_profile = ret.get('profile', {}) or ret.get('user', {})
        location = initial_profile.get('location') if initial_profile else None
        try:
            user = User.objects.get(Q(email=email) | Q(username=email))
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'email': _('The email or username you entered do not belong to any account')})

        if not user.check_password(password):
            raise serializers.ValidationError({'password': _('The password you entered is incorrect')})
        self.instance = user
        if location:
            location_controller.update_profile_location(user.ap, location)
        return ret


class ShoutitPageSerializer(serializers.Serializer):
    page_category = PageCategorySerializer()
    page_name = serializers.CharField(max_length=60, min_length=2)
    name = serializers.CharField(max_length=70)
    first_name = serializers.CharField(min_length=2, max_length=30, required=False)
    last_name = serializers.CharField(min_length=1, max_length=30, required=False)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, max_length=30)
    profile = ProfileDetailSerializer(required=False)

    def to_internal_value(self, data):
        if not data:
            data = {}
        name = data.get('name', 'user')
        names = name.split()
        if len(names) >= 2:
            data['first_name'] = " ".join(names[0:-1])
            data['last_name'] = names[-1]
        elif len(names) >= 1:
            data['first_name'] = names[0]
            data['last_name'] = random.randint(0, 999)
        else:
            data['first_name'] = 'user'
            data['last_name'] = random.randint(0, 999)

        ret = super(ShoutitPageSerializer, self).to_internal_value(data)
        return ret

    def validate_email(self, email):
        email = email.lower()
        if User.exists(email=email):
            raise serializers.ValidationError(_('This email is used by another account'))
        return email

    def create(self, validated_data):
        request = self.context.get('request')
        initial_profile = validated_data.get('profile', {}) or validated_data.get('user', {})
        initial_profile['ip'] = get_real_ip(request)
        user, page = page_controller.user_and_page_from_shoutit_page_data(validated_data, initial_profile,
                                                                          request.is_test)
        # Set the page admin user for serializing the admin property of this page
        request.page_admin_user = user
        return user, page


class ShoutitGuestSerializer(serializers.Serializer):
    user = GuestSerializer(required=False)
    profile = GuestSerializer(required=False)

    def to_internal_value(self, data):
        ret = super(ShoutitGuestSerializer, self).to_internal_value(data)
        request = self.context.get('request')
        initial_guest_user = ret.get('profile', {}) or ret.get('user', {})
        push_tokens = initial_guest_user.get('push_tokens', {})
        apns = push_tokens.get('apns')
        gcm = push_tokens.get('gcm')
        try:
            if apns:
                user = User.objects.get(apnsdevice__registration_id=apns, is_guest=True)
            elif gcm:
                user = User.objects.get(gcmdevice__registration_id=gcm, is_guest=True)
            else:
                raise User.DoesNotExist()
        except User.DoesNotExist:
            initial_guest_user['ip'] = get_real_ip(request)
            # Create user
            user = user_controller.user_from_guest_data(initial_gust_user=initial_guest_user, is_test=request.is_test)
            # Set Push Tokens
            if push_tokens:
                user.update_push_tokens(push_tokens, 'v3')

        # Todo: Check when this case happens
        if not user:
            raise serializers.ValidationError(_('Could not create guest account'))
        self.instance = user
        return ret


class ShoutitVerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)

    def validate_email(self, email):
        user = self.context.get('request').user
        email = email.lower()
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            raise serializers.ValidationError(_('This email is used by another account'))
        return email

    def to_internal_value(self, data):
        ret = super(ShoutitVerifyEmailSerializer, self).to_internal_value(data)
        user = self.context.get('request').user
        email = ret.get('email')
        # if the email changed the model will take care of sending the verification email
        if email:
            user.email = email.lower()
            user.save(update_fields=['email', 'is_activated'])
        else:
            user.send_verification_email()
        return ret


class ShoutitResetPasswordSerializer(serializers.Serializer):
    email = serializers.CharField()

    def to_internal_value(self, data):
        ret = super(ShoutitResetPasswordSerializer, self).to_internal_value(data)
        email = ret.get('email').lower()
        try:
            user = User.objects.get(Q(email=email) | Q(username=email))
            if not user.is_active:
                raise AuthenticationFailed('User inactive or deleted.')
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {'email': _('The email or username you entered do not belong to any account')})
        self.instance = user
        return ret


class ShoutitChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6, max_length=30)
    new_password2 = serializers.CharField(min_length=6, max_length=30)

    def to_internal_value(self, data):
        if not data:
            data = {}
        user = self.context.get('request').user
        if not user.is_password_set:
            data['old_password'] = 'ANYTHING'
        ret = super(ShoutitChangePasswordSerializer, self).to_internal_value(data)
        new_password = ret.get('new_password')
        new_password2 = ret.get('new_password2')

        if new_password != new_password2:
            raise serializers.ValidationError({'new_password': _('New passwords did not match')})

        user.set_password(new_password)
        user.save(update_fields=['password'])
        # Todo: Do we really need to log the user in?
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.context.get('request'), user)
        return ret

    def validate_old_password(self, value):
        user = self.context.get('request').user
        if user.is_password_set:
            if not user.check_password(value):
                raise serializers.ValidationError(_('Old password is incorrect'))


class ShoutitSetPasswordSerializer(serializers.Serializer):
    reset_token = serializers.CharField()
    new_password = serializers.CharField(min_length=6, max_length=30)
    new_password2 = serializers.CharField(min_length=6, max_length=30)

    def to_internal_value(self, data):
        ret = super(ShoutitSetPasswordSerializer, self).to_internal_value(data)
        new_password = ret.get('new_password')
        new_password2 = ret.get('new_password2')
        if new_password != new_password2:
            raise serializers.ValidationError({'new_password': _('New passwords did not match')})
        user = self.instance
        user.set_password(new_password)
        user.save(update_fields=['password'])
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.context.get('request'), user)
        return ret

    def validate_reset_token(self, value):
        try:
            user = ConfirmToken.objects.get(type=TOKEN_TYPE_RESET_PASSWORD, token=value, is_disabled=False).user
            if not user.is_active:
                raise AuthenticationFailed(_('Account inactive or deleted'))
            self.instance = user
        except ConfirmToken.DoesNotExist:
            raise serializers.ValidationError(_('Reset token is invalid'))


class ProfileDeactivationSerializer(serializers.Serializer):
    password = serializers.CharField()

    def to_internal_value(self, data):
        ret = super(ProfileDeactivationSerializer, self).to_internal_value(data)
        password = ret.get('password')
        user = self.context.get('user')
        if not user.check_password(password):
            raise serializers.ValidationError({'password': _('The password you entered is incorrect')})
        user.update(is_active=False)
        return ret


class SMSCodeSerializer(serializers.Serializer):
    sms_code = serializers.CharField(max_length=10, min_length=6)

    def to_internal_value(self, data):
        ret = super(SMSCodeSerializer, self).to_internal_value(data)
        sms_code = ret.get('sms_code').upper()
        try:
            dbcl_conversation = DBCLConversation.objects.get(sms_code__iexact=sms_code)
            self.instance = dbcl_conversation.to_user
        except DBCLConversation.DoesNotExist:
            raise serializers.ValidationError({'sms_code': _('Invalid sms_code')})
        return ret
