from datetime import datetime
import re
from django import forms
from django.utils.encoding import force_unicode
from django.utils.html import escape, conditional_escape
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.forms.extras.widgets import SelectDateWidget
from apps.shoutit import constants, utils
from apps.shoutit.constants import ExperienceState
from apps.shoutit.controllers import user_controller
from apps.shoutit.models import Currency, BusinessProfile, BusinessCategory, BusinessCreateApplication
from common.tagged_cache import TaggedCache


def _get_currencies():
    currencies = TaggedCache.get('perma|currencies')
    if not currencies:
        currencies = tuple((c.Code, c.Code) for c in Currency.objects.all())
        TaggedCache.set('perma|currencies', currencies, timeout=10 * 356 * 24 * 60 * 60)
    return currencies


class LoginForm(forms.Form):
    username_or_email = forms.CharField(label=_('Username or Email'), max_length=75, min_length=3)
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput())

    def clean(self):
        if not user_controller.ValidateCredentials(self.data['username_or_email'].strip(), self.data['password'].strip()):
            raise ValidationError(_('Invalid credentials.'))
        return self.cleaned_data

    def clean_username_or_email(self):
        username_or_email =  self.data['username_or_email'].strip()
        return username_or_email


class RecoverForm(forms.Form):
    username_or_email = forms.CharField(label=_('Username or Email'), max_length=75, min_length=3)
    def clean(self):
        if not user_controller.GetUser(self.data['username_or_email'].strip()) and not user_controller.GetUserByEmail(self.data['username_or_email'].strip()):
            raise ValidationError(_('Invalid credentials.'))
        return self.cleaned_data


class ShoutForm(forms.Form):
    price = forms.FloatField(label=_('Price'), min_value=0.0)
    currency = forms.ChoiceField(label = _('Currency'), choices=_get_currencies(), required=True)
    name = forms.CharField(label=_('Name'), max_length=120)
    description = forms.CharField(label=_('Description'), widget=forms.Textarea(), max_length=200)
    tags = forms.CharField(label=_('Tags'))
    image = forms.ImageField(label=_('Image'), required=False)
    location = forms.CharField(label=_('Location'))
    country = forms.CharField(label=_('Country'))
    city = forms.CharField(label=_('City'))
    address = forms.CharField(label=_('Address'), required = False)


class ExperienceForm(forms.Form):
    text = forms.CharField(label=_('Text'), widget=forms.Textarea(), max_length=200)
    state = forms.TypedChoiceField(choices=ExperienceState.values.items(), widget=forms.RadioSelect, coerce=int)
    username = forms.CharField(label='Business', max_length=20, min_length=3, widget=forms.HiddenInput, required=False)


class CommentForm(forms.Form):
    text = forms.CharField(label=_('Text'), widget=forms.Textarea(attrs = {'cols': '40', 'rows': '2'}), max_length=300)


class ReportForm(forms.Form):
    text = forms.CharField(label=_('Text'), widget=forms.Textarea(attrs = {'cols': '40', 'rows': '2'}), max_length=300)


class ItemForm(forms.Form):
    price = forms.FloatField(label=_('Price'), min_value=0.0)
    currency = forms.ChoiceField(label = _('Currency'), choices=_get_currencies(), required=True)
    name = forms.CharField(label=_('Name'), max_length=120)
    description = forms.CharField(label=_('Description'), widget=forms.Textarea(), max_length=512)
    image = forms.ImageField(label=_('Image'), required=False)


class SignUpForm(forms.Form):
    #	username = forms.CharField(label='Username', max_length=20, min_length=3)
    email = forms.EmailField(label=_('Email'))
    firstname = forms.CharField(label=_('First Name'), max_length=20, min_length=3)
    lastname = forms.CharField(label=_('Last Name'), max_length=20, min_length=3)
    #	mobile = forms.CharField(label='Phone', max_length=20, min_length=3, required= False)
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput())
    confirm_password = forms.CharField(label=_('Confirm Password'), widget=forms.PasswordInput())

    #	def clean_username(self):
    #		username = self.data['username']
    #		if not re.search(r'^\w+$', username):
    #			raise forms.ValidationError('Username can only contain alphanumeric characters and the underscore.')
    #		try:
    #			User.objects.get(username = username)
    #		except ObjectDoesNotExist:
    #			return username
    #		raise forms.ValidationError('Username is already taken.')

    def clean_email(self):
        email = self.data['email'].strip()
        if email is None or email == '':
            return email
        try:
            User.objects.get(email = email)
        except ObjectDoesNotExist:
            return email
        raise forms.ValidationError(_('Email is already in use by another user.'))

    def clean_confirm_password(self):
        password = self.data['password'].strip()
        confirm_password = self.data['confirm_password'].strip()
        if password != confirm_password:
            raise forms.ValidationError(_('Passwords don\'t match.'))
        return confirm_password

#	def clean_mobile(self):
#		mobile = self.data['mobile']
#		if mobile is None or mobile == '':
#			return mobile
#		try:
#			User.objects.get(Profile__Mobile = mobile)
#		except ObjectDoesNotExist:
#			return mobile
#		raise forms.ValidationError('Phone number is already in use by another user')

sex_choices = (
(1, _('Male')),
(0, _('Female')),
)


class ExtenedSignUpSSS(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ExtenedSignUpSSS, self).__init__(*args, **kwargs)
        if self.initial is not None:
            if self.initial.has_key('mobile'):
                self.fields['mobile'].widget.attrs['disabled'] = True

    username = forms.CharField(label=_('Username'), max_length=20, min_length=3,  required=True)
    firstname = forms.CharField(label=_('First Name'), max_length=20, min_length=3, required=True)
    lastname = forms.CharField(label=_('Last Name'), max_length=20, min_length=3, required=True)
    email = forms.EmailField(label=_('Email'),  required=True)
    mobile = forms.CharField(label=_('Phone'), max_length=20, min_length=3, required=False)
    birthdate = forms.DateField(label=_('Birth Date'), widget=SelectDateWidget(years=range(datetime.now().year, 1920, -1)),required=True)
    sex = forms.ChoiceField(label=_('Sex'), choices= sex_choices, required=True)
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput())
    confirm_password = forms.CharField(label=_('Confirm Password'), widget=forms.PasswordInput())
    tokentype = forms.CharField(label='tt', widget=forms.HiddenInput())

    def clean_username(self):
        username = self.data['username'].strip()
        if not username or username == '':
            return username
        if not re.search(r'^\w+$', username):
            raise forms.ValidationError(_('Username can only contain alphanumeric characters and the underscore.'))
        try:
            user = User.objects.get(username = username)
            if username == self.initial['username']:
                return username
            else:
                raise forms.ValidationError(_('Username is already taken.'))
        except ObjectDoesNotExist:
            return username

    def clean_email(self):
        email = self.data['email'].strip()
        if email is None or email == '':
            return email
        try:
            User.objects.get(email = email)
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


class ReActivate(forms.Form):
    username = forms.CharField(label=_('Username'), required=False, widget=forms.HiddenInput())
    email = forms.EmailField(label=_('Email'), required=True)

    def clean_email(self):
        email = self.data['email'].strip()
        if email is None or email == '':
            return email
        try:
            user = User.objects.get(email = email)
            if user.username == self.data['username'].strip():
                return email
            else:
                raise forms.ValidationError(_('Email is already in use by another user.'))
        except ObjectDoesNotExist:
            return email


class ExtenedSignUp(forms.Form):
    def __init__(self, *args, **kwargs):
        super(ExtenedSignUp, self).__init__(*args, **kwargs)
        if self.initial is not None:
            if self.initial.has_key('mobile'):
                self.fields['mobile'].widget.attrs['disabled'] = True
            elif self.initial.has_key('email'):
                self.fields['email'].widget.attrs['disabled'] = True

    username = forms.CharField(label=_('Username'), max_length=20, min_length=3, required=False)
    email = forms.EmailField(label=_('Email'), required=False)
    mobile = forms.CharField(label=_('Phone'), max_length=20, min_length=3, required=False)
    birthdate = forms.DateField(label=_('Birth Date'), widget=SelectDateWidget(years=range(datetime.now().year, 1920, -1)), required=True)
    sex = forms.ChoiceField(label=_('Sex'), choices=sex_choices, required=True)
    tokentype = forms.CharField(label='tt', widget=forms.HiddenInput(), required=False)

    def clean_username(self):
        username = self.data['username'].strip()
        if not username or username == '':
            return username
        if not re.search(r'^\w+$', username):
            raise forms.ValidationError(_('Username can only contain alphanumeric characters and the underscore.'))
        try:
            user = User.objects.get(username = username)
            if user.email == self.initial['email'].strip():
                return username
            else:
                raise forms.ValidationError(_('Username is already taken.'))
        except ObjectDoesNotExist:
            return username

    def clean_mobile(self):
        mobile = self.data['mobile'].strip()
        try:
            type = int(self.data['tokentype'])
        except KeyError:
            type = int(self.initial['tokentype'])
        if type == constants.TOKEN_TYPE_HTML_NUM:
            return mobile
        if mobile is None or mobile == '':
            return mobile
        try:
            User.objects.get(Profile__Mobile = mobile)
        except ObjectDoesNotExist:
            return mobile
        raise forms.ValidationError(_('Phone number is already in use by another user'))


class APISignUpForm(forms.Form):
    username = forms.CharField(label=_('Username'), max_length=20, min_length=3)
    email = forms.EmailField(label=_('Email'))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput, max_length=64)
    confirm_password = forms.CharField(label=_('Confirm Password'), widget=forms.PasswordInput, max_length=64)
    mobile = forms.CharField(label=_('Mobile'), max_length=64, required=False)
    firstname = forms.CharField(label=_('First Name'), max_length=20, min_length=3, required=True)
    lastname = forms.CharField(label=_('Last Name'), max_length=20, min_length=3, required=True)
    birthdate = forms.DateField(label=_('Birth Date'), widget=SelectDateWidget(years=range(datetime.now().year, 1920, -1)),required=True)
    sex = forms.ChoiceField(label=_('Sex'), choices= sex_choices, required=True)

    def clean_username(self):
        username = self.data['username'].strip()
        if not re.search(r'^\w+$', username):
            raise forms.ValidationError(_('Username can only contain alphanumeric characters and the underscore.'))
        try:
            User.objects.get(username = username)
        except ObjectDoesNotExist:
            return username
        raise forms.ValidationError(_('Username is already taken.'))

    def clean_email(self):
        email = self.data['email'].strip()
        try:
            User.objects.get(email = email)
        except ObjectDoesNotExist:
            return email
        raise forms.ValidationError(_('Email is already in use by another user.'))

    def clean_confirm_password(self):
        password = self.data['password'].strip()
        cpassword = self.data['confirm_password'].strip()
        if password != cpassword:
            raise forms.ValidationError(_('Passwords don\'t match.'))
        return cpassword


class MessageForm(forms.Form):
    text = forms.CharField(label=_('Text'), widget=forms.Textarea(),max_length=1024, required=True)


class BusinessEditProfileForm(forms.Form):
    username = forms.CharField(label=_('Username'),required=False)
    name = forms.CharField(label=_('First Name'), max_length=20, min_length=3, required=False)
    email = forms.EmailField(label=_('Email'), required=False)
    mobile = forms.CharField(label=_('Phone'), max_length=20, min_length=3, required=False)
    website = forms.CharField(label=_('Website'),required=False)

    password = forms.CharField(label=_('New password'), widget=forms.PasswordInput(), required=False)
    password_confirm = forms.CharField(label=_('Confirm new password'), widget=forms.PasswordInput(), required=False)

    bio = forms.CharField(label=_('Bio'), widget=forms.Textarea(), max_length=512, required=False)

    location = forms.CharField(label=_('Location'))
    country = forms.CharField(label=_('Country'))
    city = forms.CharField(label=_('City'))
    address = forms.CharField(label=_('Address'), required = False)


class UserEditProfileForm(forms.Form):
    username = forms.CharField(label=_('Username'),required=False)
    firstname = forms.CharField(label=_('First Name'), max_length=20, min_length=3, required=False)
    lastname = forms.CharField(label=_('Last Name'), max_length=20, min_length=3, required=False)
    email = forms.EmailField(label=_('Email'), required=False)
    mobile = forms.CharField(label=_('Phone'), max_length=20, min_length=3, required=False)

    password = forms.CharField(label=_('New Password'), widget=forms.PasswordInput(), required=False)
    password_confirm = forms.CharField(label=_('Confirm new password'), widget=forms.PasswordInput(), required=False)

    bio = forms.CharField(label=_('Bio'), widget=forms.Textarea(), max_length=512, required=False)

    birthdate = forms.DateField(label=_('Birth Date'), widget=SelectDateWidget(years=range(datetime.now().year, 1920, -1)), initial=datetime.today()
                                ,required=False)
    sex = forms.ChoiceField(label=_('Sex'), choices= sex_choices, required=False)

    def clean_firstname(self):
        firstname = self.data['firstname'].strip()
        fname = utils.safe_string(firstname)
        if not fname or len(fname) == 0:
            return firstname
        else:
            raise forms.ValidationError(_('Please, keep it clean.'))

    def clean_lastname(self):
        lastname = self.data['lastname'].strip()
        lname = utils.safe_string(lastname)
        if not lname or len(lname) == 0:
            return lastname
        else:
            raise forms.ValidationError(_('Please, keep it clean.'))

    def clean_bio(self):
        bioinfo = self.data['bio'].strip()
        bio = utils.safe_string(self.data['bio'].strip())
        if not bio or len(bio) == 0:
            return bioinfo
        else:
            raise forms.ValidationError(_('Please, keep it clean.'))

    def clean_username(self):
        username = self.data['username'].strip()
        if not username or username == '':
            return username
        if not re.search(r'^\w+$', username):
            raise forms.ValidationError(_('Username can only contain alphanumeric characters and the underscore.'))
        try:
            user = User.objects.get(username = username)
            if user.email == self.initial['email'].strip():
                return username
            else:
                raise forms.ValidationError(_('Username is already taken.'))
        except ObjectDoesNotExist:
            return username
        #		raise forms.ValidationError('Username is already taken.')

    def clean_email(self):
        email = self.data['email'].strip()
        if email is None or email == '':
            return email
        try:
            user = User.objects.get(email = email)
            if user.username == self.initial['username'].strip():
                return email
            else:
                raise forms.ValidationError(_('Email is already in use by another user.'))
        except ObjectDoesNotExist:
            return email

        #	def clean_old_password(self):
        #		if (self.data['password'] or self.data['password_confirm']) and not self.data['old_password']:
        #			raise forms.ValidationError('Old password is required to change your password.')
        #		elif self.data['old_password']:
        #			user = User.objects.get(username=self.data['username'])
        #			if user.check_password(self.data['old_password']):
        #				return self.data['old_password']
        #			raise forms.ValidationError('Invalid old password.')
        #		else:
        #			return self.data['old_password']

    def clean_password_confirm(self):
        if self.data['password'].strip() == self.data['password_confirm'].strip():
            return self.data['password_confirm'].strip()
        raise forms.ValidationError(_('Passwords don\'t match.'))

    def clean_password(self):
        if self.data['password'].strip() == self.data['password_confirm'].strip():
            return self.data['password_confirm'].strip()
        raise forms.ValidationError(_('Passwords don\'t match.'))

    def clean_mobile(self):
        mobile = self.data['mobile'].strip()
        if mobile is None or mobile == '':
            return mobile
        try:
            user = User.objects.get(Profile__Mobile = mobile)
            if user.username == self.initial['username'].strip():
                return mobile
            User.objects.get(Profile__Mobile = mobile)
        except ObjectDoesNotExist:
            return mobile
        raise forms.ValidationError(_('Phone number is already in use by another user'))

    def clean_birthdate(self):
        try:
            birthdate = datetime.strptime(self.data['birthdate_year'] +'-'+ self.data['birthdate_month'] +'-'+ self.data['birthdate_day'], '%Y-%m-%d')
        except ValueError, e:
            return None
        if birthdate and birthdate > datetime.now():
            raise forms.ValidationError(_('Birthdate is not valid.'))
        return birthdate


class BusinessSelect (forms.Select):
    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_unicode(option_value)
        selected_html = (option_value in selected_choices) and u' selected="selected"' or ''
        return u'<option value="%s"%s id="%s">%s</option>' % (
        escape(option_value), selected_html,
        BusinessCategory.objects.get(pk = int(option_value)).SourceID,
        conditional_escape(force_unicode(option_label)))


class CreateTinyBusinessForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CreateTinyBusinessForm, self).__init__(*args, **kwargs)
        if self.initial is not None:
            if self.initial.has_key('name') and self.initial['name'] and len(self.initial['name'].strip()):
                self.fields['name'].widget.attrs['disabled'] = True
            if self.initial.has_key('email') and self.initial['email'] and len(self.initial['email'].strip()):
                self.fields['email'].widget.attrs['disabled'] = True


    name = forms.CharField(label=_('Name'))
    category = forms.ChoiceField(
        choices=BusinessCategory.objects.get_tuples(),
        widget=BusinessSelect(), required=False
    )
    location = forms.CharField(label=_('Location'), required = False)
    country = forms.CharField(label=_('Country'), required = False)
    city = forms.CharField(label=_('City'), required = False)
    address = forms.CharField(label=_('Address'), required = False)

    source = forms.CharField(label=_('Source'), required = False)
    source_id = forms.CharField(label=_('SourceID'), required = False)


class BusinessSignUpForm(CreateTinyBusinessForm):
    #	name = forms.CharField(label=_('Name'))
    #	username = forms.CharField(label=_('Username'),required=False)
    email = forms.EmailField(label=_('Email'))
    phone = forms.CharField(label=_('Phone'), max_length=20, min_length=3)
    website = forms.CharField(label=_('Website'))
    description = forms.CharField(label=_('Description'), widget=forms.Textarea(), max_length=200, required=False)

    #	location = forms.CharField(label=_('Location'))
    #	country = forms.CharField(label=_('Country'))
    #	city = forms.CharField(label=_('City'))
    #	address = forms.CharField(label=_('Address'), required = False)

    def clean_email(self):
        email = self.data['email'].strip()
        if email is None or email == '':
            return email
        try:
            User.objects.get(email = email)
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
            BusinessProfile.objects.get(Phone = phone)
            if not BusinessCreateApplication.objects.filter(Phone = phone).count():
                return phone
        except ObjectDoesNotExist:
            return phone

        raise forms.ValidationError(_('Phone is already in use by another user.'))


class BusinessTempSignUpForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(BusinessTempSignUpForm, self).__init__(*args, **kwargs)
        if self.initial is not None:
            if self.initial.has_key('name'):
                self.fields['name'].widget.attrs['disabled'] = True

    name = forms.CharField(label=_('Name'), max_length=120, required=False)
    email = forms.EmailField(label=_('Email'))
    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput())
    confirm_password = forms.CharField(label=_('Confirm Password'), widget=forms.PasswordInput())

    def clean_email(self):
        email = self.data['email'].strip()
        if email is None or email == '':
            return email
        try:
            User.objects.get(email = email)
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

    name = forms.CharField(label=_('Name'), max_length=120, required=False)
    username = forms.CharField(label=_('Username'))
    email = forms.EmailField(label=_('Email'), required= False)
    phone = forms.CharField(label=_('Phone'), max_length=20, min_length=3, required=False)

    password = forms.CharField(label=_('Password'), widget=forms.PasswordInput())
    confirm_password = forms.CharField(label=_('Confirm Password'), widget=forms.PasswordInput())

    def clean_username(self):
        username = self.data['username'].strip()
        if not username or username == '':
            return username
        if not re.search(r'^\w+$', username):
            raise forms.ValidationError(_('Username can only contain alphanumeric characters and the underscore.'))
        try:
            User.objects.get(username = username)
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
    price = forms.FloatField(label = _('Price'), min_value=0.0)
    currency = forms.ChoiceField(label = _('Currency'), choices=_get_currencies(), required=True)
    name = forms.CharField(label = _('Name'), max_length=120)
    description = forms.CharField(label = _('Description'), widget=forms.Textarea(), max_length=200)
    tags = forms.CharField(label = _('Tags'))
    location = forms.CharField(label = _('Location'))
    country = forms.CharField(label = _('Country'))
    city = forms.CharField(label = _('City'))
    expiry_date = forms.DateTimeField(label = _('Expiry Date'), required=True)
    min_buyers = forms.IntegerField(label = _('Minimum number of buyers'), initial=0, required=False)
    max_buyers = forms.IntegerField(label = _('Maximum number of buyers'), required=False)
    original_price = forms.FloatField(label = _('Original price'), min_value=0.0)
    valid_from = forms.DateTimeField(label = _('Valid From'), required = False)
    valid_to = forms.DateTimeField(label = _('Valid To'), required = False)

    def clean_original_price(self):
        if self.cleaned_data.has_key('original_price'):
            if self.cleaned_data.has_key('price') and self.cleaned_data['original_price'] < self.cleaned_data['price']:
                raise forms.ValidationError(_('Original price can\'t be less than the price itself.'))
            return self.cleaned_data['original_price']
        return None

    def clean_max_buyers(self):
        if self.cleaned_data.has_key('max_buyers') and self.cleaned_data.has_key('min_buyers') and self.cleaned_data['max_buyers'] and self.cleaned_data['max_buyers'] < self.cleaned_data['min_buyers']:
            raise forms.ValidationError(_('Maximum number of buyres can\'t be less than the minimum number of buyers.'))
        return self.cleaned_data.has_key('max_buyers') and self.cleaned_data['max_buyers'] or None

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.has_key('expiry_date') and self.cleaned_data['expiry_date'] or None
        if expiry_date and expiry_date < datetime.now():
            raise forms.ValidationError(_('Expiry date can\'t be in the past.'))
        return expiry_date

    def clean_valid_to(self):
        try:
            valid_to = self.cleaned_data.has_key('valid_to') and self.cleaned_data['valid_to'] or None
        except ValueError, e:
            raise forms.ValidationError(_('Invalid expiry date.'))
        if valid_to and valid_to < datetime.now():
            raise forms.ValidationError(_('Valid to date can\'t be in the past.'))
        valid_from = self.cleaned_data.has_key('valid_from') and self.cleaned_data['valid_from'] or None
        if valid_to and valid_from and valid_from >= valid_to:
            raise forms.ValidationError(_('Valid to date can\'t be before valid from date.'))
        return valid_to