"""

"""
from django.utils.translation import ugettext_lazy as _
from hvad.contrib.restframework import TranslatableModelSerializer
from rest_framework import serializers, exceptions as drf_exceptions

from shoutit.controllers import page_controller
from shoutit.models import PageCategory
from shoutit.models.page import PageVerification, PAGE_VERIFICATION_STATUS_WAITING
from shoutit.utils import blank_to_none
from .base import RecursiveSerializer, empty_char_input
from .profile import ObjectProfileActionSerializer, ProfileDetailSerializer, MiniProfileSerializer


class PageCategorySerializer(TranslatableModelSerializer):
    name = serializers.CharField(read_only=True, source='_local_name')
    slug = serializers.CharField()
    children = RecursiveSerializer(many=True, read_only=True)

    class Meta:
        model = PageCategory
        fields = ['id', 'name', 'slug', 'image', 'children']
        extra_kwargs = {'name': {'read_only': True}, 'image': {'read_only': True}}

    def to_representation(self, instance):
        ret = super(PageCategorySerializer, self).to_representation(instance)
        blank_to_none(ret, ['image', 'cover', 'icon'])
        return ret

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = {'slug': data}
        super(PageCategorySerializer, self).to_internal_value(data)
        return self.instance

    def validate_slug(self, slug):
        try:
            self.instance = PageCategory.objects.get(slug=slug)
        except (PageCategory.DoesNotExist, AttributeError):
            raise serializers.ValidationError(_("PageCategory with slug '%(slug)s' does not exist") % {'slug': slug})


class PageDetailSerializer(ProfileDetailSerializer):
    name = serializers.CharField(max_length=30, min_length=2)
    creator = MiniProfileSerializer(source='page.creator', read_only=True)
    category = PageCategorySerializer(source='page.category', required=False)
    is_published = serializers.BooleanField(source='page.is_published', default=False)
    is_verified = serializers.BooleanField(source='page.is_verified', read_only=True)
    about = serializers.CharField(source='page.about', max_length=150, **empty_char_input)
    description = serializers.CharField(source='page.description', max_length=1000, **empty_char_input)
    phone = serializers.CharField(source='page.phone', max_length=30, **empty_char_input)
    founded = serializers.CharField(source='page.founded', max_length=50, **empty_char_input)
    impressum = serializers.CharField(source='page.impressum', max_length=2000, **empty_char_input)
    overview = serializers.CharField(source='page.overview', max_length=1000, **empty_char_input)
    mission = serializers.CharField(source='page.mission', max_length=1000, **empty_char_input)
    general_info = serializers.CharField(source='page.general_info', max_length=1000, **empty_char_input)

    class Meta(ProfileDetailSerializer.Meta):
        parent_fields = ProfileDetailSerializer.Meta.fields
        fields = parent_fields + ('creator', 'category', 'about', 'is_published', 'is_verified', 'description', 'phone',
                                  'founded', 'impressum', 'overview', 'mission', 'general_info')

    def to_representation(self, instance):
        ret = super(PageDetailSerializer, self).to_representation(instance)
        blank_to_none(ret, ['about', 'description', 'phone', 'founded', 'impressum', 'overview', 'mission',
                            'general_info'])
        return ret


class AddAdminSerializer(ObjectProfileActionSerializer):
    success_message = _("Added %(name)s to the admins of this page")

    def condition(self, instance, actor, profile):
        return True

    def update(self, instance, validated_data):
        profile = self.fields['profile'].instance
        if not instance.is_admin(profile):
            instance.add_admin(profile)
        else:
            self.success_message = _("%(name)s is already admin in this page")
        return instance


class RemoveAdminSerializer(ObjectProfileActionSerializer):
    error_message = _("%(name)s is not admin in this page")
    success_message = _("Removed %(name)s from the admins of this page")

    def condition(self, instance, actor, profile):
        return instance.is_admin(profile)

    def update(self, instance, validated_data):
        profile = self.fields['profile'].instance
        instance.remove_admin(profile)
        return instance


class CreatePageSerializer(serializers.Serializer):
    page_category = PageCategorySerializer()
    page_name = serializers.CharField(max_length=60, min_length=2)

    def create(self, validated_data):
        request = self.context.get('request')
        name = validated_data['page_name']
        category = validated_data['page_category']
        page = page_controller.create_page(creator=request.user, name=name, category=category)
        # Set the user and page admin user for correctly serializing this page and its admin property
        request.page_admin_user = request.user
        request._user = page
        return page

    def to_representation(self, instance):
        return PageDetailSerializer(instance=instance, context=self.context).data


class PageVerificationSerializer(serializers.Serializer):
    success_message_created = _('Your business verification request has been submitted')
    success_message_updated = _('Your business verification request has been updated')

    status = serializers.CharField(source='get_status_display', read_only=True)
    business_name = serializers.CharField(max_length=50, min_length=2)
    business_email = serializers.EmailField()
    contact_person = serializers.CharField(max_length=50, min_length=2)
    contact_number = serializers.CharField(max_length=20, min_length=8)
    images = serializers.ListField(child=serializers.URLField())

    def to_internal_value(self, data):
        ret = super(PageVerificationSerializer, self).to_internal_value(data)
        user = self.context['request'].user
        if not self.instance.is_admin(user):
            raise drf_exceptions.PermissionDenied()
        return ret

    def update(self, instance, validated_data):
        validated_data.update({
            'admin': self.context['request'].user,
            'status': PAGE_VERIFICATION_STATUS_WAITING
        })
        page_verification, created = PageVerification.objects.update_or_create(defaults=validated_data, page=instance)
        page_verification.created = created
        return page_verification

    def to_representation(self, instance):
        ret = super(PageVerificationSerializer, self).to_representation(instance)
        if hasattr(instance, 'created'):
            ret.update({'success': self.success_message_created if instance.created else self.success_message_updated})
        return ret
