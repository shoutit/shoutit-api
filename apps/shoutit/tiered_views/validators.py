import uuid
from jsonschema import Draft4Validator, FormatChecker

from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from common.constants import *
from apps.shoutit.models import ConfirmToken, Item, GalleryItem, Profile, Business, Trade
from apps.shoutit.controllers import shout_controller, business_controller, experience_controller, comment_controller, event_controller
from apps.shoutit.controllers import tag_controller
from apps.shoutit.controllers.user_controller import get_profile
from apps.shoutit.controllers import message_controller
from apps.shoutit.forms import MessageForm, UserEditProfileForm, ShoutForm, ExtenedSignUp, ExperienceForm, ItemForm, \
    BusinessEditProfileForm, CreateTinyBusinessForm, CommentForm
from apps.shoutit.tiers import ValidationResult as VR, RESPONSE_RESULT_ERROR_404, RESPONSE_RESULT_ERROR_NOT_ACTIVATED, \
    RESPONSE_RESULT_ERROR_NOT_LOGGED_IN, RESPONSE_RESULT_ERROR_BAD_REQUEST, RESPONSE_RESULT_ERROR_FORBIDDEN


def form_errors(schema_errors):
    f_errors = []
    for se in schema_errors:
        f_errors.append(('.'.join(list(se.path)), se.message))
    return f_errors


def uuid_validator(uuid_string):
    try:
        uuid.UUID(uuid_string)
        return VR(True)
    except Exception as e:
        print e
        return VR(False)


def object_exists_validator(function, using_uuid, error_message='object does not exist', *args, **kwargs):
    try:
        if using_uuid:
            if not uuid_validator(args[0]):
                raise ValueError()

        result = function(*args, **kwargs)
        if not result:
            raise ObjectDoesNotExist()

        return VR(True, data=result)

    except (ValueError, ObjectDoesNotExist):
        return VR(False, messages=[('error', error_message)], errors=[RESPONSE_RESULT_ERROR_404])


# todo: use this function, add possibility of more owners
def access_validator(request, obj, owner, extras=None):
    if request.method in ['POST', 'PUT', 'DELETE'] and request.user != owner:
        return VR(False, messages=[('error', _('Not allowed.'))], errors=[RESPONSE_RESULT_ERROR_FORBIDDEN])
    else:
        data = {obj.__class__.__name__: obj}
        if isinstance(extras, dict):
            data.update(extras)
        return VR(True, data=data)


def form_validator(request, form_class, message='You have entered some invalid input.', initial=None):
    initial = initial or {}
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, initial=initial)
        if form.is_valid():
            return VR(True, data={'form': form})
        else:
            return VR(False, messages=[('error', _(message))], form_errors=form.errors)
    return VR(True)


def shout_form_validator(request, form_class, message='You have entered some invalid input.', initial=None):
    initial = initial or {}
    validation_result = form_validator(request, form_class, _(message), initial)
    if validation_result.valid:
        if not request.user.is_active and Trade.objects.get_valid_trades().filter(
                OwnerUser=request.user).count() >= settings.MAX_SHOUTS_INACTIVE_USER:
            return VR(False, messages=[
                ('error', _('Please, activate your account to add more shouts (check your email for activation link)'))],
                errors=[RESPONSE_RESULT_ERROR_NOT_ACTIVATED])
    return validation_result


def send_message_validator(request, shout_id, conversation_id):
    # 1 - validating the form
    result = form_validator(request, MessageForm)
    if result.valid:

        # 2 - validating the shout
        result = object_exists_validator(shout_controller.get_post, True, _('Shout does not exist.'), shout_id, True, True)
        if result.valid:
            shout = result.data
            conversation = None

            # 3 - if there is no conversation_id, make sure user is not sending to himself
            if not conversation_id and request.user.pk == shout.OwnerUser.pk:
                return VR(False, messages=[('error', _("You can't start a conversation about your own shout."))])

            # 4 - if there is conversation_id, make sure the conversation exists
            if conversation_id:
                result = object_exists_validator(message_controller.get_conversation, True, _('Conversation does not exist.'),
                                                 conversation_id, request.user)
                if result.valid:
                    conversation = result.data

            result.data = {'shout': shout, 'conversation': conversation}

    return result


def profile_picture_validator(request, profile_type='', size='', tag_name='', username=''):
    result = VR(valid=False)

    if profile_type == 'user':
        result = user_profile_validator(request, username)

    elif profile_type == 'tag':
        result = object_exists_validator(tag_controller.get_tag, False, _('Tag %(tag_name)s does not exist.') % {'tag_name': tag_name},
                                         tag_name)

    return result


def user_edit_profile_validator(request, username, email):
    result = object_exists_validator(get_profile, False, _('User %(username)s does not exist.') % {'username': username}, username)
    if result:
        profile = result.data
        if username == request.user.username or request.user.is_staff:
            init = {'username': username, 'email': email}
            if profile and isinstance(profile, Profile):
                result = form_validator(request, UserEditProfileForm, initial=init)
            elif profile and isinstance(profile, Business):
                result = form_validator(request, BusinessEditProfileForm, initial=init)
            else:
                result = VR(False, messages=[('error', _('User %(username)s does not exist.') % {'username': username})],
                            errors=[RESPONSE_RESULT_ERROR_404])
            return result
        else:
            return VR(False, messages=[('error', _("You don't have permissions to edit this profile."))])
    return result


def read_conversation_validator(request, conversation_id):
    result = object_exists_validator(message_controller.get_conversation, True, _('Conversation does not exist.'), conversation_id,
                                     request.user)
    if not result:
        return result
    conversation = result.data
    if not (request.user == conversation.FromUser or request.user == conversation.ToUser):
        return VR(False, errors=[RESPONSE_RESULT_ERROR_FORBIDDEN],
                  messages=[('error', _("You don't have permissions to view this conversation."))])
    return VR(True, data={'conversation': conversation})


def conversation2_validator(request, conversation_id):
    result = object_exists_validator(message_controller.get_conversation2, True, _('Conversation does not exist.'), conversation_id)
    if not result:
        return result
    conversation = result.data
    if request.user not in conversation.users.all():
        return VR(False, messages=[('error', _("You don't have permissions to view this conversation."))])

    return VR(True, data={'conversation': conversation})


def message_validator(message):
    result = VR(True)
    # todo: validator for json object attributes
    if 'attachments' in message:
        attachments = message['attachments']
        if isinstance(attachments, list) and len(attachments) > 0:
            for idx, attachment in enumerate(attachments):

                if False:  # todo: validation using jsonschema
                    result = VR(False, form_errors={
                        "attachments": ["attachments[%s] is missing valid 'content_type' or 'object_id'." % str(idx)]
                    })
                    return result

        else:
            result = VR(False, form_errors={"attachments": ["This field should be a non-empty list of {attachment}."]})

    elif not ('text' in message and unicode(message['text']).strip()):
        result = VR(False, form_errors={"text": ["This field is required and can't be empty."]})

    return result


def reply_in_conversation_validator(request, conversation_id):
    message = request.json_data
    result = message_validator(message)
    if not result:
        return result

    result = object_exists_validator(message_controller.get_conversation, True, _('Conversation does not exist.'), conversation_id,
                                     request.user)
    if result:
        conversation = result.data
        if request.user.pk != conversation.FromUser.pk and request.user.pk != conversation.ToUser.pk:
            return VR(False, messages=[('error', _("You don't have permissions to view this conversation."))])
        result.data = {
            'conversation': conversation,
            'text': 'text' in message and unicode(message['text']).strip() or None,
            'attachments': 'attachments' in message and message['attachments'] or None
        }
    return result


def reply_in_conversation2_validator(request, conversation_id):
    message = request.json_data
    result = message_validator(message)
    if not result:
        return result

    conversation2_validation = conversation2_validator(request, conversation_id)
    if not conversation2_validation:
        return conversation2_validation
    conversation = conversation2_validation.data['conversation']

    result.data = {
        'conversation': conversation,
        'text': 'text' in message and unicode(message['text']).strip() or None,
        'attachments': 'attachments' in message and message['attachments'] or None
    }
    return result


def reply_to_shout_validator(request, shout_id):
    message = request.json_data
    result = message_validator(message)
    if not result:
        return result

    result = object_exists_validator(shout_controller.get_post, True, _('Shout does not exist.'), shout_id)
    if result:
        shout = result.data
        if request.user.pk == shout.OwnerUser.pk:
            return VR(False, messages=[('error', _("You can't start a conversation about your own shout."))])
        result.data = {
            'shout': shout,
            'text': 'text' in message and message['text'] or None,
            'attachments': 'attachments' in message and message['attachments'] or None
        }
    return result


def modify_shout_validator(request, shout_id):
    if not request.user.is_authenticated():
        return VR(False, errors=[RESPONSE_RESULT_ERROR_NOT_LOGGED_IN], messages=[('error', _('You are not signed in.'))])

    result = object_exists_validator(shout_controller.get_post, True, _('Shout does not exist.'), shout_id, True, True)
    if result:
        shout = result.data
        if shout.OwnerUser == request.user or request.user.is_staff:
            return VR(True, data={'shout': shout})
        else:
            return VR(False, errors=[RESPONSE_RESULT_ERROR_FORBIDDEN],
                      messages=[('error', _('You are not allowed to modify this shout.'))])
    else:
        return result


def edit_shout_validator(request, shout_id):
    modify_validation = modify_shout_validator(request, shout_id)
    if not modify_validation:
        return modify_validation
    shout = modify_validation.data['shout']

    form_validation = form_validator(request, ShoutForm)
    if not form_validation:
        return form_validation
    form = form_validation.data['form']

    # this contains the shout in its data to be used
    return VR(True, data={'shout': shout, 'form': form})


def delete_message_validator(request, conversation_id, message_id):
    result = object_exists_validator(message_controller.get_conversation, True, _('Conversation does not exist.'), conversation_id)
    if not result:
        return result

    conversation = result.data
    if not (request.user == conversation.FromUser or request.user == conversation.ToUser):
        return VR(False, messages=[('error', _("You don't have permissions to delete this conversation."))])

    return object_exists_validator(message_controller.get_message, True, _('Message does not exist.'), message_id)


def message2_validator(request, conversation_id, message_id):
    conversation2_validation = conversation2_validator(request, conversation_id)
    if not conversation2_validation:
        return conversation2_validation
    conversation = conversation2_validation.data['conversation']

    result = object_exists_validator(message_controller.get_message2, True, _('Message does not exist.'), message_id)
    if not result:
        return result
    message = result.data
    if message.conversation != conversation:
        return VR(False, messages=[('error', _("the message doesn't belong to the conversation."))])

    return VR(True, data={'conversation': conversation, 'message': message})


def delete_conversation_validator(request, conversation_id):
    result = object_exists_validator(message_controller.get_conversation, True, _('Conversation does not exist.'), conversation_id)
    conversation = result.data
    if not (request.user == conversation.FromUser or request.user == conversation.ToUser):
        return VR(False, messages=[('error', _("You don't have permissions to delete this conversation."))])

    return result


def user_profile_validator(request, username, *args, **kwargs):
    if username == '@me' and request.user.is_authenticated():
        username = request.user.username
    elif username == '@me':
        return VR(False, messages=[('error', _('You are not signed in.'))], errors=[RESPONSE_RESULT_ERROR_NOT_LOGGED_IN])

    result = object_exists_validator(get_profile, False, _('User %(username)s does not exist.') % {'username': username}, username)
    if not result:
        return result
    else:
        profile = result.data
        if not profile.user.is_active and profile.user != request.user and not request.user.is_staff:
            return VR(False, messages=[('error', _('User %(username)s is not active yet.') % {'username': username})],
                                    errors=[RESPONSE_RESULT_ERROR_NOT_ACTIVATED])
        if request.method in ['POST', 'PUT', 'DELETE'] and request.user != profile.user:
            return VR(False, messages=[('error', _('Not allowed.'))], errors=[RESPONSE_RESULT_ERROR_FORBIDDEN])

        return VR(True, data={'profile': profile})


def user_profile_edit_validator(request, username, *args, **kwargs):
    profile_validation = user_profile_validator(request, username, *args, **kwargs)
    if not profile_validation:
        return profile_validation

    instance = request.json_data
    schema = {
        'type': 'object',
        'properties': {
            'username': {'type': 'string', 'minLength': 2, 'maxLength': 30, 'pattern': '^[\w.]+$'},
            'first_name': {"type": "string", "minLength": 2, "maxLength": 30},
            'last_name': {'type': 'string', 'minLength': 2, 'maxLength': 30},
            'email': {'type': 'string', 'minLength': 2, 'maxLength': 254, 'format': 'email'},
            'bio': {'type': 'string', 'maxLength': 512},
            'sex': {'type': 'boolean'},
        },
        'additionalProperties': False,
        'minProperties': 1
    }
    v = Draft4Validator(schema, format_checker=FormatChecker())
    errors = [e for e in v.iter_errors(instance)]
    if not errors:
        return VR(True, data={'profile': profile_validation.data['profile'], 'new_attributes': instance})
    return VR(False, form_errors=form_errors(errors))


def push_validator(request, username, push_type, *args, **kwargs):
    if request.method == 'POST':
        token = 'token' in request.json_data and request.json_data['token'] or None
        if not token:
            return VR(False, messages=[('error', _('Invalid Push token'))], errors=[RESPONSE_RESULT_ERROR_BAD_REQUEST])
        return VR(True, data={'token': token})
    else:
        return VR(True)


def activate_api_validator(request, token, *args, **kwargs):
    if not token:
        return VR(False, {'token': [_('This field is required.')]}, [RESPONSE_RESULT_ERROR_BAD_REQUEST],
                                [('error', _('You have entered some invalid input.'))])
    t = ConfirmToken.getToken(token, False, False)
    if not t:
        return VR(False, {'token': [_('Invalid activation token.')]}, [RESPONSE_RESULT_ERROR_BAD_REQUEST],
                  [('error', _('You have entered some invalid input.'))])
    return form_validator(request, ExtenedSignUp, initial={'email': request.user.email, 'tokentype': TOKEN_TYPE_API_EMAIL.value})


def shout_owner_view_validator(request, shout_id):
    find_muted = find_expired = request.user.is_authenticated()
    result = object_exists_validator(shout_controller.get_post, True, _('Shout does not exist.'), shout_id, find_muted, find_expired)

    if result:
        shout = shout_controller.get_post(shout_id, True, True)
        if shout.is_expired:
            if shout.OwnerUser != request.user and not request.user.is_staff:
                return VR(False, messages=[('error', _('Shout does not exist.'))], errors=[RESPONSE_RESULT_ERROR_404])
    return result


# def post_experience_validator(request,business_name,*args,**kwargs):
# result = form_validator(request, ExperienceForm)
# if result:
# business = business_controller.GetBusiness(business_name)
# if not business:
#			return VR(False, messages=[('error', _('Business dose not exist.'))],)
#	return result


def share_experience_validator(request, exp_id, *args, **kwargs):
    result = object_exists_validator(shout_controller.get_post, True, _('Experience dose not exist.'), exp_id)
    if result:
        experience = experience_controller.GetExperience(exp_id, request.user, detailed=True)
        if not experience.canShare:
            return VR(False, messages=[('error', _('You can not share this experience.'))])
    return result


def experience_validator(request, *args, **kwargs):
    exp_frm = form_validator(request, ExperienceForm, initial=kwargs.has_key('initial') and kwargs['initial'] or {})
    if not args and (not kwargs.has_key('username') or not kwargs['username']):
        extended_exp_frm = form_validator(request, CreateTinyBusinessForm, initial=kwargs.has_key('initial') and kwargs['initial'] or {})
        exp_frm.form_errors.update(extended_exp_frm.form_errors)
        exp_frm.valid = exp_frm.valid and extended_exp_frm.valid
        exp_frm.messages = exp_frm.messages if exp_frm.messages else extended_exp_frm.messages
    return VR(exp_frm.valid, messages=exp_frm.messages, form_errors=exp_frm.form_errors)


def experience_view_validator(request, exp_id, *args, **kwargs):
    return object_exists_validator(experience_controller.GetExperience, True, _('Experience does not exist.'), exp_id, request.user, True)


def edit_experience_validator(request, exp_id, *args, **kwargs):
    result = object_exists_validator(shout_controller.get_post, True, _('Experience dose not exist.'), exp_id)
    if result.valid:
        experience = experience_controller.GetExperience(exp_id, request.user, detailed=True)
        if not experience.canEdit:
            return VR(False, messages=[('error', _('You can not edit this experience.'))])
    return result


def delete_gallery_item_validator(request, item_id, *args, **kwargs):
    result = object_exists_validator(GalleryItem.objects.filter, True, _('Gallery Item dose not exist.'), Item=Item.objects.get(pk=item_id),
                                     IsDisable=False)
    if result:
        gallery_item = GalleryItem.objects.filter(Item=Item.objects.get(pk=item_id), IsDisable=False)[0]
        try:
            # galleries = request.user.Business.Galleries.all()
            galleries = business_controller.GetBusiness('business').Galleries.all()
            gallery = galleries[0] if galleries else None
            if not gallery_item.Gallery == gallery:
                VR(False, messages=[('error', _('You do not have permission to delete this item'))])
        except ValueError, e:
            return VR(False, messages=[('error', _('You do not have permission to delete this item'))])
    return result


def add_gallery_item_validator(request, business_name, *args, **kwargs):
    result = form_validator(request, ItemForm)
    if result:
        business = business_controller.GetBusiness(business_name)
        business_galleries = business.Galleries.all()
        gallery = business_galleries[0] if business_galleries else None
        try:
            if request.user.Business != business:
                return VR(False, messages=[('error', _('You do not have permission to add item.'))], )
        except:
            return VR(False, messages=[('error', _('You do not have permission to add item.'))], )

        if not gallery:
            return VR(False, messages=[('error', _('Gallery does not exist.'))], )
    return result


def comment_on_post_validator(request, post_id, form_class):
    result = form_validator(request, CommentForm)
    if result:
        result = object_exists_validator(shout_controller.get_post, True, _('Experience dose not exist.'), post_id)
    return result


def delete_comment_validator(request, comment_id):
    result = object_exists_validator(comment_controller.GetCommentByID, True, _('Comment dose not exist.'), comment_id)
    if result:
        comment = comment_controller.GetCommentByID(comment_id)
        if comment.OwnerUser != request.user:
            return VR(False, messages=[('error', _('You do not have permission to delete this comment'))])
    return result


def delete_event_validator(request, event_id):
    result = object_exists_validator(event_controller.get_event, True, _('Activity dose not exist.'), event_id)
    if result:
        event = event_controller.get_event(event_id)
        if event.OwnerUser != request.user:
            return VR(False, messages=[('error', _('You do not have permission to delete this activity'))])
    return result