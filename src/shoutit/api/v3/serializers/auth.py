"""

"""
from __future__ import unicode_literals

import random

from django.contrib.auth import login
from django.db.models import Q
from ipware.ip import get_real_ip
from push_notifications.models import APNSDevice, GCMDevice
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from common.constants import TOKEN_TYPE_RESET_PASSWORD
from shoutit.controllers import facebook_controller, gplus_controller, user_controller, location_controller
from shoutit.models import User, DBCLConversation, ConfirmToken
from .profile import ProfileDetailSerializer, GuestSerializer


# Todo: change `user` to `profile` in all serializers
class FacebookAuthSerializer(serializers.Serializer):
    facebook_access_token = serializers.CharField(max_length=512)
    user = ProfileDetailSerializer(required=False)

    def to_internal_value(self, data):
        ret = super(FacebookAuthSerializer, self).to_internal_value(data)
        request = self.context.get('request')
        facebook_access_token = ret.get('facebook_access_token')
        initial_user = ret.get('user', {})
        initial_user['ip'] = get_real_ip(request)
        user = facebook_controller.user_from_facebook_auth_response(facebook_access_token, initial_user, request.is_test)
        self.instance = user
        return ret


class GplusAuthSerializer(serializers.Serializer):
    gplus_code = serializers.CharField(max_length=1000)
    user = ProfileDetailSerializer(required=False)

    def to_internal_value(self, data):
        ret = super(GplusAuthSerializer, self).to_internal_value(data)
        request = self.context.get('request')
        gplus_code = ret.get('gplus_code')
        initial_user = ret.get('user', {})
        initial_user['ip'] = get_real_ip(request)
        user = gplus_controller.user_from_gplus_code(gplus_code, initial_user, request.client, request.is_test)
        self.instance = user
        return ret


class ShoutitSignupSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=70)
    first_name = serializers.CharField(min_length=2, max_length=30, required=False)
    last_name = serializers.CharField(min_length=1, max_length=30, required=False)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, max_length=30)
    user = ProfileDetailSerializer(required=False)

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
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Email is already used by another user')
        return email

    def create(self, validated_data):
        initial_user = validated_data.get('user', {})
        request = self.context.get('request')
        initial_user['ip'] = get_real_ip(request)
        user = user_controller.user_from_shoutit_signup_data(validated_data, initial_user, request.is_test)
        return user


class ShoutitLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()
    user = ProfileDetailSerializer(required=False)

    def to_internal_value(self, data):
        ret = super(ShoutitLoginSerializer, self).to_internal_value(data)
        email = ret.get('email').lower()
        password = ret.get('password')
        initial_user = ret.get('user', {})
        location = initial_user.get('location') if initial_user else None
        try:
            user = User.objects.get(Q(email=email) | Q(username=email))
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'The email or username you entered do not belong to any account'})

        if not user.check_password(password):
            raise serializers.ValidationError({'password': 'The password you entered is incorrect'})
        self.instance = user
        if location:
            location_controller.update_profile_location(user.ap, location)
        return ret


class ShoutitGuestSerializer(serializers.Serializer):
    user = GuestSerializer(required=False)

    def to_internal_value(self, data):
        ret = super(ShoutitGuestSerializer, self).to_internal_value(data)
        request = self.context.get('request')
        initial_guest_user = ret.get('user', {})
        push_tokens = initial_guest_user.get('push_tokens', {})
        apns = push_tokens.get('apns')
        gcm = push_tokens.get('gcm')
        try:
            if apns:
                user = User.objects.get(apnsdevice__registration_id=apns)
            elif gcm:
                user = User.objects.get(gcmdevice__registration_id=gcm)
            else:
                raise User.DoesNotExist()
        except User.DoesNotExist:
            initial_guest_user['ip'] = get_real_ip(request)
            user = user_controller.user_from_guest_data(initial_gust_user=initial_guest_user, is_test=request.is_test)
            if apns:
                # delete devices with same apns_token
                APNSDevice.objects.filter(registration_id=apns).delete()
                # create new device for user with apns_token
                APNSDevice(registration_id=apns, user=user).save()
            elif gcm:
                # delete devices with same gcm_token
                GCMDevice.objects.filter(registration_id=gcm).delete()
                # create new device for user with gcm_token
                GCMDevice(registration_id=gcm, user=user).save()
        # Todo: Check when this case happens
        if not user:
            raise serializers.ValidationError("Could not create guest account")
        self.instance = user
        return ret


class ShoutitVerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)

    def validate_email(self, email):
        user = self.context.get('request').user
        email = email.lower()
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            raise serializers.ValidationError('Email is already used by another account')
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
            raise serializers.ValidationError({'email': 'The email or username you entered do not belong to any account'})
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
            raise serializers.ValidationError({'new_password': 'New passwords did not match'})

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
                raise serializers.ValidationError('Old password is incorrect')


class ShoutitSetPasswordSerializer(serializers.Serializer):
    reset_token = serializers.CharField()
    new_password = serializers.CharField(min_length=6, max_length=30)
    new_password2 = serializers.CharField(min_length=6, max_length=30)

    def to_internal_value(self, data):
        ret = super(ShoutitSetPasswordSerializer, self).to_internal_value(data)
        new_password = ret.get('new_password')
        new_password2 = ret.get('new_password2')
        if new_password != new_password2:
            raise serializers.ValidationError({'new_password': 'New passwords did not match'})
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
                raise AuthenticationFailed('Account inactive or deleted')
            self.instance = user
        except ConfirmToken.DoesNotExist:
            raise serializers.ValidationError('Reset token is invalid')


class ProfileDeactivationSerializer(serializers.Serializer):
    password = serializers.CharField()

    def to_internal_value(self, data):
        ret = super(ProfileDeactivationSerializer, self).to_internal_value(data)
        password = ret.get('password')
        user = self.context.get('user')
        if not user.check_password(password):
            raise serializers.ValidationError({'password': 'The password you entered is incorrect'})
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
            raise serializers.ValidationError({'sms_code': "Invalid sms_code"})
        return ret