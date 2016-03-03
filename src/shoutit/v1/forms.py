from __future__ import unicode_literals

import re

from django import forms
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.translation import ugettext_lazy as _

from shoutit.controllers import user_controller
from shoutit.models import User, Currency, Business, BusinessCategory, BusinessCreateApplication


def _get_currencies():
    currencies = tuple((c.code, c.code) for c in Currency.objects.all())
    return currencies


class RecoverForm(forms.Form):
    username_or_email = forms.CharField(label=_('Username or Email'), max_length=254, min_length=2)

    def clean(self):
        if not user_controller.get_profile(
                self.data['username_or_email'].strip()) and not user_controller.GetUserByEmail(self.data['username_or_email'].strip()):
            raise ValidationError(_('Invalid credentials.'))
        return self.cleaned_data


gender_choices = (
    (1, _('Male')),
    (0, _('Female')),
)


class BusinessEditProfileForm(forms.Form):
    username = forms.CharField(label=_('Username'), required=False)
    name = forms.CharField(label=_('First Name'), max_length=30, min_length=2, required=False)
    email = forms.EmailField(label=_('Email'), max_length=254, required=False)
    mobile = forms.CharField(label=_('Phone'), max_length=20, min_length=3, required=False)
    website = forms.CharField(label=_('Website'), required=False)

    password = forms.CharField(label=_('New password'), widget=forms.PasswordInput(),
                               required=False)
    password_confirm = forms.CharField(label=_('Confirm new password'),
                                       widget=forms.PasswordInput(), required=False)

    bio = forms.CharField(label=_('bio'), widget=forms.Textarea(), max_length=512, required=False)

    location = forms.CharField(label=_('Location'))
    country = forms.CharField(label=_('Country'))
    city = forms.CharField(label=_('City'))
    address = forms.CharField(label=_('Address'), required=False)


class BusinessSelect(forms.Select):
    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_unicode(option_value)
        selected_html = (option_value in selected_choices) and u' selected="selected"' or ''
        return u'<option value="%s"%s id="%s">%s</option>' % (
            escape(option_value), selected_html,
            BusinessCategory.objects.get(pk=int(option_value)).SourceID,
            conditional_escape(force_unicode(option_label)))


class CreateTinyBusinessForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CreateTinyBusinessForm, self).__init__(*args, **kwargs)
        if self.initial is not None:
            if 'name' in self.initial and self.initial['name'] and len(
                    self.initial['name'].strip()):
                self.fields['name'].widget.attrs['disabled'] = True
            if 'email' in self.initial and self.initial['email'] and len(
                    self.initial['email'].strip()):
                self.fields['email'].widget.attrs['disabled'] = True

    name = forms.CharField(label=_('name'))
    category = forms.ChoiceField(
        choices=BusinessCategory.objects.get_tuples(),
        widget=BusinessSelect(), required=False
    )
    location = forms.CharField(label=_('Location'), required=False)
    country = forms.CharField(label=_('Country'), required=False)
    city = forms.CharField(label=_('City'), required=False)
    address = forms.CharField(label=_('Address'), required=False)

    source = forms.CharField(label=_('Source'), required=False)
    source_id = forms.CharField(label=_('SourceID'), required=False)


class BusinessSignUpForm(CreateTinyBusinessForm):
    # name = forms.CharField(label=_('name'))
    # username = forms.CharField(label=_('Username'),required=False)
    email = forms.EmailField(label=_('Email'))
    phone = forms.CharField(label=_('Phone'), max_length=20, min_length=3)
    website = forms.CharField(label=_('Website'))
    description = forms.CharField(label=_('Description'), widget=forms.Textarea(), max_length=200,
                                  required=False)

    # location = forms.CharField(label=_('Location'))
    # country = forms.CharField(label=_('country'))
    # city = forms.CharField(label=_('City'))
    # address = forms.CharField(label=_('Address'), required = False)

    def clean_email(self):
        email = self.data['email'].strip()
        if email is None or email == '':
            return email
        try:
            User.objects.get(email=email)
            if email == self.initial['email'].strip():
                return email
        except ObjectDoesNotExist:
            return email
        raise forms.ValidationError(_('Email is already in use by another user.'))

    def clean_phone(self):
        phone = self.data['phone'].strip()
        if phone is None or phone == '':
            return phone
        try:
            Business.objects.get(Phone=phone)
            if not BusinessCreateApplication.objects.filter(Phone=phone).count():
                return phone
        except ObjectDoesNotExist:
            return phone

        raise forms.ValidationError(_('Phone is already in use by another user.'))


class BusinessTempSignUpForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BusinessTempSignUpForm, self).__init__(*args, **kwargs)
        if self.initial is not None:
            if 'name' in self.initial:
                self.fields['name'].widget.attrs['disabled'] = True

    name = forms.CharField(label=_('name'), max_length=120, required=False)
    email = forms.EmailField(label=_('Email'))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput())
    confirm_password = forms.CharField(label=_('Confirm Password'), widget=forms.PasswordInput())

    def clean_email(self):
        email = self.data['email'].strip()
        if email is None or email == '':
            return email
        try:
            User.objects.get(email=email)
        except ObjectDoesNotExist:
            return email
        raise forms.ValidationError(_('Email is already in use by another user.'))

    def clean_password_confirm(self):
        if self.data['password'].strip() == self.data['confirm_password'].strip():
            return self.data['confirm_password'].strip()
        raise forms.ValidationError(_('Passwords don\'t match.'))

    def clean_password(self):
        if self.data['password'].strip() == self.data['confirm_password'].strip():
            return self.data['confirm_password'].strip()
        raise forms.ValidationError(_('Passwords don\'t match.'))


class StartBusinessForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(StartBusinessForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['disabled'] = True
        self.fields['email'].widget.attrs['disabled'] = True
        self.fields['phone'].widget.attrs['disabled'] = True

    name = forms.CharField(label=_('name'), max_length=120, required=False)
    username = forms.CharField(label=_('Username'), max_length=30)
    email = forms.EmailField(label=_('Email'), required=False, max_length=254)
    phone = forms.CharField(label=_('Phone'), max_length=20, min_length=3, required=False)

    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput())
    confirm_password = forms.CharField(label=_('Confirm Password'), widget=forms.PasswordInput())

    def clean_username(self):
        username = self.data['username'].strip()
        if not username or username == '':
            return username
        if not re.search(r'^\w+$', username):
            raise forms.ValidationError(
                _('Username can only contain alphanumeric characters and the underscore.'))
        try:
            User.objects.get(username=username)
        except ObjectDoesNotExist:
            return username
        raise forms.ValidationError(_('Username is already taken.'))

    def clean_password_confirm(self):
        if self.data['password'].strip() == self.data['confirm_password'].strip():
            return self.data['confirm_password'].strip()
        raise forms.ValidationError(_('Passwords don\'t match.'))

    def clean_password(self):
        if self.data['password'].strip() == self.data['confirm_password'].strip():
            return self.data['confirm_password'].strip()
        raise forms.ValidationError(_('Passwords don\'t match.'))


class DealForm(forms.Form):
    price = forms.FloatField(label=_('Price'), min_value=0.0)
    currency = forms.ChoiceField(label=_('Currency'), choices=_get_currencies(), required=True)
    name = forms.CharField(label=_('name'), max_length=120)
    description = forms.CharField(label=_('Description'), widget=forms.Textarea(), max_length=200)
    tags = forms.CharField(label=_('Tags'))
    location = forms.CharField(label=_('Location'))
    country = forms.CharField(label=_('Country'))
    city = forms.CharField(label=_('City'))
    expiry_date = forms.DateTimeField(label=_('Expiry Date'), required=True)
    min_buyers = forms.IntegerField(label=_('Minimum number of buyers'), initial=0, required=False)
    max_buyers = forms.IntegerField(label=_('Maximum number of buyers'), required=False)
    original_price = forms.FloatField(label=_('Original price'), min_value=0.0)
    valid_from = forms.DateTimeField(label=_('Valid From'), required=False)
    valid_to = forms.DateTimeField(label=_('Valid To'), required=False)

    def clean_original_price(self):
        if 'original_price' in self.cleaned_data:
            if 'price' in self.cleaned_data and self.cleaned_data['original_price'] < \
                    self.cleaned_data['price']:
                raise forms.ValidationError(
                    _('Original price can\'t be less than the price itself.'))
            return self.cleaned_data['original_price']
        return None

    def clean_max_buyers(self):
        if 'max_buyers' in self.cleaned_data and 'min_buyers' in self.cleaned_data and \
                self.cleaned_data['max_buyers'] and self.cleaned_data['max_buyers'] < self.cleaned_data['min_buyers']:
            raise forms.ValidationError(_('Maximum number of buyres can\'t be less than the minimum number of buyers.'))
        return 'max_buyers' in self.cleaned_data and self.cleaned_data['max_buyers'] or None

    def clean_expiry_date(self):
        expiry_date = 'expiry_date' in self.cleaned_data and self.cleaned_data[
            'expiry_date'] or None
        if expiry_date and expiry_date < timezone.now():
            raise forms.ValidationError(_('Expiry date can\'t be in the past.'))
        return expiry_date

    def clean_valid_to(self):
        try:
            valid_to = 'valid_to' in self.cleaned_data and self.cleaned_data['valid_to'] or None
        except ValueError:
            raise forms.ValidationError(_('Invalid expiry date.'))
        if valid_to and valid_to < timezone.now():
            raise forms.ValidationError(_('Valid to date can\'t be in the past.'))
        valid_from = 'valid_from' in self.cleaned_data and self.cleaned_data['valid_from'] or None
        if valid_to and valid_from and valid_from >= valid_to:
            raise forms.ValidationError(_('Valid to date can\'t be before valid from date.'))
        return valid_to
