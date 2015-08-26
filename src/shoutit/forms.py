"""

"""
from __future__ import unicode_literals
import json
from django import forms
from django.contrib.postgres.forms import SplitArrayField
from django.forms import URLField
from shoutit.models import PushBroadcast, Item
from common.constants import DeviceOS, COUNTRIES


class PushBroadcastForm(forms.ModelForm):
    countries = forms.MultipleChoiceField(choices=COUNTRIES, required=False)
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


class ItemForm(forms.ModelForm):
    images = SplitArrayField(URLField(required=False), size=10, remove_trailing_nulls=True)

    class Meta:
        model = Item
        fields = '__all__'
