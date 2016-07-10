"""

"""
from __future__ import unicode_literals
import json
import uuid

import boto
from django import forms
from django.conf import settings
from django.contrib.postgres.forms import SplitArrayField
from django.core.exceptions import ValidationError
from django.forms import URLField
from hvad.forms import TranslatableModelForm

from common.utils import process_tag
from shoutit.models import PushBroadcast
from common.constants import DeviceOS, COUNTRY_CHOICES
from django.utils.translation import string_concat


class PushBroadcastForm(forms.ModelForm):
    countries = forms.MultipleChoiceField(choices=COUNTRY_CHOICES, required=False)
    devices = forms.MultipleChoiceField(choices=DeviceOS.choices, required=False)

    def save(self, commit=True):
        return super(PushBroadcastForm, self).save(commit=commit)

    def clean_devices(self):
        devices = self.cleaned_data['devices']
        return [int(d) for d in devices]

    def clean_conditions(self):
        conditions = self.cleaned_data['conditions']
        try:
            conditions = json.loads(conditions)
        except:
            raise forms.ValidationError("Invalid Json for conditions!")

        countries = self.cleaned_data.get('countries')
        if countries:
            conditions['countries'] = countries

        devices = self.cleaned_data.get('devices')
        if devices:
            conditions['devices'] = devices

        return json.dumps(conditions)

    def clean_data(self):
        data = self.cleaned_data['data']
        try:
            json.loads(data)
        except:
            raise forms.ValidationError("Invalid Json for data!")
        return data

    class Meta:
        model = PushBroadcast
        fields = ('message', 'countries', 'devices', 'conditions', 'data')


class ShoutitSplitArrayField(SplitArrayField):
    def clean(self, value):
        cleaned_data = []
        errors = []
        if not any(value) and self.required:
            raise ValidationError(self.error_messages['required'])
        max_size = max(self.size, len(value))
        for i in range(max_size):
            item = value[i]
            try:
                cleaned_data.append(self.base_field.clean(item))
                errors.append(None)
            except ValidationError as error:
                errors.append(ValidationError(
                    string_concat(self.error_messages['item_invalid'], ' '.join(error.messages)),
                    code='item_invalid',
                    params={'nth': i},
                ))
                cleaned_data.append(None)
        if self.remove_trailing_nulls:
            null_index = None
            for i, value in reversed(list(enumerate(cleaned_data))):
                if value in self.base_field.empty_values:
                    null_index = i
                else:
                    break
            if null_index is not None:
                cleaned_data = cleaned_data[:null_index]
                errors = errors[:null_index]
        errors = list(filter(None, errors))
        if errors:
            raise ValidationError(errors)
        return cleaned_data


class ItemForm(forms.ModelForm):
    images = ShoutitSplitArrayField(URLField(required=False), required=False, size=10, remove_trailing_nulls=True)


class ImageFileChangeForm(TranslatableModelForm):
    image_file = forms.FileField(required=False)

    def clean_image_file(self):
        image_file = self.cleaned_data.get('image_file')
        if not image_file:
            return
        s3 = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = s3.get_bucket('shoutit-tag-image-original')
        slug = self.cleaned_data.get('slug', 'tag')
        filename = "%s-%s.jpg" % (uuid.uuid4(), process_tag(slug))
        key = bucket.new_key(filename)
        key.set_metadata('Content-Type', 'image/jpg')
        key.set_contents_from_file(image_file)
        s3_image_url = 'https://tag-image.static.shoutit.com/%s' % filename
        self.cleaned_data['image'] = s3_image_url
