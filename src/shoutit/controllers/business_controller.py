from __future__ import unicode_literals
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from shoutit.models import User
from common.constants import (TOKEN_LONG, TOKEN_TYPE_EMAIL_BUSINESS_ACTIVATE,
                              FILE_TYPE_BUSINESS_DOCUMENT,
                              TOKEN_TYPE_EMAIL_BUSINESS_CONFIRM,
                              BUSINESS_CONFIRMATION_STATUS_ACCEPTED, BUSINESS_SOURCE_TYPE_NONE)
from shoutit.models import (Business, ConfirmToken, StoredFile, BusinessConfirmation,
                            BusinessSource, BusinessCategory,
                            BusinessCreateApplication, PredefinedCity)
from shoutit.controllers.user_controller import set_last_token, give_user_permissions
from shoutit.controllers import email_controller
from shoutit.permissions import ACTIVATED_BUSINESS_PERMISSIONS
from shoutit import utils
from shoutit.utils import to_seo_friendly


def GetBusiness(username):
    if not isinstance(username, str) and not isinstance(username, unicode):
        return None
    try:
        q = Business.objects.filter(user__username__iexact=username)
        if q:
            return q[0]
        else:
            return None
    except ValueError:
        return None


def CreateTinyBusinessProfile(name, category, latitude=0.0, longitude=0.0, country=None, city=None,
                              address=None,
                              source_type=BUSINESS_SOURCE_TYPE_NONE, source_id=None):
    username = utils.generate_username()
    while len(User.objects.filter(username=username)):
        username = utils.generate_username()
    password = utils.generate_confirm_token(TOKEN_LONG)
    email = '%s@%s.com' % (username, 'shoutit')

    django_user = User.objects.create_user(username, email, password)
    # django_user.first_name = name

    django_user.is_active = True
    django_user.save()

    cat = None
    if category:
        try:
            cat = BusinessCategory.objects.get(pk=int(category))
        except ObjectDoesNotExist:
            cat = None

    bp = Business(user=django_user, Category=cat, name=name,
                  latitude=latitude, longitude=longitude, country=country, city=city,
                  address=address)
    bp.image = '/static/img/_user_male.png'
    bp.save()

    if not PredefinedCity.objects.filter(city=city):
        encoded_city = to_seo_friendly(unicode.lower(unicode(city)))
        PredefinedCity(city=city, city_encoded=encoded_city, country=country, latitude=latitude,
                       longitude=longitude).save()

    if source_id is not None:
        source = BusinessSource(business=bp, Source=source_type, SourceID=source_id)
        source.save()
    return bp


def ClaimTinyBusiness(request, tiny_username, email, phone, website, about=None, documents=[]):
    business = GetBusiness(tiny_username)
    if not business:
        return None
    if business.Confirmed:
        return None

    django_user = business.user
    django_user.email = email
    django_user.save()

    business.Phone = phone
    business.Website = website
    business.About = about

    if len(documents):
        confirmation = BusinessConfirmation(user=django_user)
        confirmation.save()
        for document in documents:
            doc = StoredFile(user=django_user, File=document, type=FILE_TYPE_BUSINESS_DOCUMENT)
            doc.save()
            confirmation.Files.add(doc)
        confirmation.save()
    django_user.save()

    business.save()

    email_controller.SendBusinessSignupEmail(django_user, email, email)

    return django_user


def SignUpTempBusiness(request, email, password, send_activation=True, business=None):
    if email is None or email == '':
        return None
    username = utils.generate_username()
    while len(User.objects.filter(username=username)):
        username = utils.generate_username()
    django_user = User.objects.create_user(username, email, password)
    app = BusinessCreateApplication(user=django_user, business=business)
    app.save()

    token = SetTempRegisterToken(django_user, email, TOKEN_LONG, TOKEN_TYPE_EMAIL_BUSINESS_ACTIVATE)

    if email is not None and send_activation:
        email_controller.SendEmail(email, {
            'name': business and business.name or "New Business",
            'email': email,
            'link': settings.SITE_LINK + token
        }, "business_temp_registration_email.html", "business_temp_registration_email.txt")

    return django_user


def SetTempRegisterToken(user, email, tokenLength, tokenType):
    token = utils.generate_confirm_token(tokenLength)
    db_token = ConfirmToken.getToken(token)
    while db_token is not None:
        token = utils.generate_confirm_token(tokenLength)
        db_token = ConfirmToken.getToken(token)
    tok = ConfirmToken(Token=token, user=user, Email=email, type=tokenType)
    tok.save()

    profile = user.BusinessCreateApplication.count() and user.BusinessCreateApplication.all()[
        0] or None
    if profile:
        profile.LastToken = tok
        profile.save()
    return token


def SignUpBusiness(request, user, name, phone, website, category, about=None,
                   latitude=0.0, longitude=0.0, country=None, city=None, address=None,
                   documents=[]):
    try:
        cat = BusinessCategory.objects.get(pk=category)
    except ObjectDoesNotExist:
        cat = None

    if user.BusinessCreateApplication.count():
        ba = user.BusinessCreateApplication.all()[0]
        if ba and ba.Business:
            ba.name = ba.Business.name
            ba.Category = ba.Business.Category
            ba.latitude = ba.Business.latitude
            ba.longitude = ba.Business.longitude
            ba.country = ba.Business.country
            ba.city = ba.Business.city
            ba.address = ba.Business.address
        else:
            ba.name = name
            ba.Category = cat
            ba.latitude = latitude
            ba.longitude = longitude
            ba.country = country
            ba.city = city
            ba.address = address

        ba.Phone = phone
        ba.About = about
        ba.Website = website

    else:
        ba = BusinessCreateApplication(user=user, Category=cat, name=name, Phone=phone, About=about,
                                       Website=website,
                                       latitude=latitude, longitude=longitude, country=country,
                                       city=city, address=address)
    ba.save()

    if not PredefinedCity.objects.filter(city=city):
        encoded_city = to_seo_friendly(unicode.lower(unicode(city)))
        PredefinedCity(city=city, city_encoded=encoded_city, country=country, latitude=latitude,
                       longitude=longitude).save()

    if len(documents):
        confirmation = BusinessConfirmation(user=user)
        confirmation.save()
        for document in documents:
            doc = StoredFile(user=user, File=document, type=FILE_TYPE_BUSINESS_DOCUMENT)
            doc.save()
            confirmation.Files.add(doc)
        confirmation.save()
    user.save()

    # bp.image = '/static/img/_user_male.png'
    # bp.save()
    email_controller.SendBusinessSignupEmail(user, user.email, ba.name)
    return ba


def EditBusiness(request, username=None, name=None, password=None, email=None, phone=None,
                 image=None,
                 about=None, website=None, latitude=0.0, longitude=0.0, country=None, city=None,
                 address=None):
    if username:
        business = GetBusiness(username)

        if name:
            business.name = name
        if password:
            business.user.set_password(password)
        if email:
            business.user.email = email
        if phone:
            business.Phone = phone
        if image:
            business.image = image
        if about:
            business.About = about
        if website:
            business.Website = website
        if latitude != 0.0:
            business.latitude = latitude
        if longitude != 0.0:
            business.longitude = longitude
        if country:
            business.country = country
        if city:
            business.city = city
        if address:
            business.address = address

        business.user.save()
        business.save()

        if not PredefinedCity.objects.filter(city=city):
            encoded_city = to_seo_friendly(unicode.lower(unicode(city)))
            PredefinedCity(city=city, city_encoded=encoded_city, country=country, latitude=latitude,
                           longitude=longitude).save()

        return business
    else:
        return None


def AcceptBusiness(request, username):
    user = username
    if isinstance(username, unicode) or isinstance(username, str):
        if User.objects.filter(username=user).count():
            user = User.objects.filter(username=user)[0]
        else:
            return
    else:
        user = username.user

    profile = user.abstract_profile

    if not user.BusinessCreateApplication.count():
        return
    ba = user.BusinessCreateApplication.all()[0]

    if ba.Business and not profile:
        ba.Business.user.password = user.password
        ba.Business.user.email = user.email
        ba.Business.user.is_staff = user.is_staff
        ba.Business.user.is_active = user.is_active
        ba.Business.user.is_superuser = user.is_superuser
        ba.Business.user.last_login = user.last_login
        ba.Business.user.date_joined = user.date_joined

        ba.Business.user.groups = user.groups.all()
        ba.Business.user.user_permissions = user.user_permissions.all()

        ba.user = ba.Business.user
        ba.LastToken = None
        ba.Business.user.BusinessConfirmations = user.BusinessConfirmations.all()
        user.delete()

        ba.Business.user.save()

        user = ba.Business.user

        ba.Business.About = ba.About
        ba.Business.Phone = ba.Phone
        ba.Business.Website = ba.Website
        ba.Business.Confirmed = True
        ba.Business.save()

    elif not ba.Business and not profile:
        bp = Business(user=user, name=ba.name, Category=ba.Category,
                      image="/static/img/_user_male.png",
                      About=ba.About, Phone=ba.Phone, Website=ba.Website, latitude=ba.latitude,
                      longitude=ba.longitude,
                      country=ba.country, city=ba.city, address=ba.address, Confirmed=True)
        bp.save()
    elif ba.Business:
        ba.Business.Confirmed = True

    ba.Status = BUSINESS_CONFIRMATION_STATUS_ACCEPTED
    ba.save()

    give_user_permissions(user, ACTIVATED_BUSINESS_PERMISSIONS)

    token = set_last_token(user, user.email, TOKEN_LONG, TOKEN_TYPE_EMAIL_BUSINESS_CONFIRM)
    email_controller.SendBusinessAcceptanceEmail(user.Business, user.email, settings.SITE_LINK + token)
