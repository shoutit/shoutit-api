from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from apps.shoutit import utils
from apps.shoutit.constants import TOKEN_TYPE_API_EMAIL, POST_TYPE_SELL, POST_TYPE_BUY
from apps.shoutit.controllers import shout_controller, business_controller, experience_controller, comment_controller, gallery_controller, event_controller
from apps.shoutit.controllers import tag_controller
from apps.shoutit.controllers import user_controller
from apps.shoutit.controllers import message_controller
from apps.shoutit.forms import MessageForm, UserEditProfileForm, ShoutForm, ExtenedSignUp, ExperienceForm, ItemForm, BusinessEditProfileForm, CreateTinyBusinessForm, CommentForm
from apps.shoutit.models import ConfirmToken, Item, GalleryItem, UserProfile, BusinessProfile, Trade
from apps.shoutit.tiers import ValidationResult, RESPONSE_RESULT_ERROR_404, RESPONSE_RESULT_ERROR_NOT_ACTIVATED, RESPONSE_RESULT_ERROR_NOT_LOGGED_IN, RESPONSE_RESULT_ERROR_BAD_REQUEST
from apps.shoutit.utils import Base62ToInt
from apps.shoutit.constants import *
import apps.shoutit.settings as settings


def object_exists_validator(function, message='', *args, **kwargs):
    try:
        result = function(*args, **kwargs)
        if not result:
            return ValidationResult(False, messages=[('error', message)], errors=[RESPONSE_RESULT_ERROR_404])
    except ObjectDoesNotExist:
        return ValidationResult(False, messages=[('error', message)], errors=[RESPONSE_RESULT_ERROR_404])
    return ValidationResult(True, data=result)


def form_validator(request, form_class, message='You have entered some invalid input.', initial={}):
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, initial=initial)
        if form.is_valid():
            return ValidationResult(True)
        else:
            return ValidationResult(False, messages=[('error', _(message))], form_errors=form.errors)
    return ValidationResult(True)


def shout_form_validator(request, form_class, message='You have entered some invalid input.', initial={}):
    validation_result = form_validator(request, form_class, _(message), initial)
    if validation_result.valid:
        if not request.user.is_active and Trade.objects.GetValidTrades().filter(OwnerUser = request.user).count() >= settings.MAX_SHOUTS_INACTIVE_USER:
            return ValidationResult(False, messages=[('error', _('Please, activate your account to add more shouts (check your email for activation link)'))], errors=[RESPONSE_RESULT_ERROR_NOT_ACTIVATED])
    return validation_result


def send_message_validator(request, shout_id, conversation_id):
    # 1 - validating the form
    result = form_validator(request, MessageForm)
    if result.valid:

        # 2 - validating the shout
        result = object_exists_validator(shout_controller.GetPost, _('Shout does not exist.'), utils.Base62ToInt(shout_id), True, True)
        if result.valid:
            shout = result.data
            conversation = None

            # 3 - if there is no conversation_id, make sure user is not sending to himself
            if not conversation_id and request.user.pk == shout.OwnerUser.pk:
                return ValidationResult(False, messages=[('error', _("You can't start a conversation about your own shout."))])

            # 4 - if there is conversation_id, make sure the conversation exists
            if conversation_id:
                result = object_exists_validator(message_controller.get_conversation, _('Conversation does not exist.'),
                                                 Base62ToInt(conversation_id), request.user)
                if result.valid:
                    conversation = result.data

            result.data = {'shout': shout, 'conversation': conversation}

    return result


def profile_picture_validator(request, type, name, size):
    result = ValidationResult(valid=False)

    if type == 'user':
        result = user_profile_validator(request, name)

    elif type == 'tag':
        result = object_exists_validator(tag_controller.GetTag, _('Tag %(tag_name)s does not exist.') % {'tag_name': name}, name)

    return result


def user_edit_profile_validator(request, username, email):
    result = object_exists_validator(user_controller.GetUser, _('User %(username)s does not exist.') % {'username': username}, username)
    if result.valid:
        if username == request.user.username or request.user.is_staff:
            init = {'username' : username, 'email' : email}
            profile = user_controller.GetProfile(request.user)
            if profile and isinstance(profile, UserProfile):
                result = form_validator(request, UserEditProfileForm, initial=init)
            elif profile and isinstance(profile, BusinessProfile):
                result = form_validator(request, BusinessEditProfileForm, initial=init)
            else:
                result = ValidationResult(False, messages=[('error', _('User %(username)s does not exist.') % {'username': username})],
                                          errors=[RESPONSE_RESULT_ERROR_404])
            return result
        else:
            return ValidationResult(False, messages=[('error', _("You don't have permissions to edit this profile."))])
    return result


def read_conversation_validator(request, conversation_id):
    result = object_exists_validator(message_controller.get_conversation, _('Conversation does not exist.'),  Base62ToInt(conversation_id),
                                     request.user)
    if result.valid:
        conversation = result.data
        if request.user.pk != conversation.FromUser_id and request.user.pk != conversation.ToUser_id:
            return ValidationResult(False, messages=[('error', _("You don't have permissions to view this conversation."))])
    return result


def message_validator(message):
    result = ValidationResult(True)
    # todo: validator for json object attributes
    if 'attachments' in message:
        attachments = message['attachments']
        if isinstance(attachments, list) and len(attachments) > 0:
            for idx, attachment in enumerate(attachments):
                if not ('content_type' in attachment and attachment['content_type'] == 'shout') \
                        or not ('object_id' in attachment and attachment['object_id']):
                    result = ValidationResult(False, form_errors={
                        "attachments": ["attachments[%s] is missing valid 'content_type' or 'object_id'." % str(idx)]
                    })
                    return result

        else:
            result = ValidationResult(False, form_errors={"attachments": ["This field should be a non-empty list of {attachment}."]})

    elif not ('text' in message and unicode(message['text']).strip()):
        result = ValidationResult(False, form_errors={"text": ["This field is required and can't be empty."]})

    return result


def reply_in_conversation_validator(request, conversation_id):
    message = request.json_data
    result = message_validator(message)
    if not result.valid:
        return result

    result = object_exists_validator(message_controller.get_conversation, _('Conversation does not exist.'), Base62ToInt(conversation_id),
                                     request.user)
    if result.valid:
        conversation = result.data
        if request.user.pk != conversation.FromUser_id and request.user.pk != conversation.ToUser_id:
            return ValidationResult(False, messages=[('error', _("You don't have permissions to view this conversation."))])
        result.data = {
            'conversation': conversation,
            'text': 'text' in message and unicode(message['text']).strip() or None,
            'attachments': 'attachments' in message and message['attachments'] or None
        }
    return result


def reply_to_shout_validator(request, shout_id):
    message = request.json_data
    result = message_validator(message)
    if not result.valid:
        return result

    result = object_exists_validator(shout_controller.GetPost, _('Shout does not exist.'), utils.Base62ToInt(shout_id))
    if result.valid:
        shout = result.data
        if request.user.pk == shout.OwnerUser.pk:
            return ValidationResult(False, messages=[('error', _("You can't start a conversation about your own shout."))])
        result.data = {
            'shout': shout,
            'text': 'text' in message and message['text'] or None,
            'attachments': 'attachments' in message and message['attachments'] or None
        }
    return result


def modify_shout_validator(request, id=None):
    if not id:
        id = request.GET[u'id']
        id = Base62ToInt(id)
    else:
        id = Base62ToInt(id)

    result = object_exists_validator(shout_controller.GetPost, _('Shout does not exist.'), id, True, True)
    if result.valid:
        if request.user.is_authenticated():
            shout = shout_controller.GetPost(id, True, True)
            if request.user.is_staff or shout.OwnerUser.pk == request.user.pk:
                return result
            else:
                return ValidationResult(False, errors=[RESPONSE_RESULT_ERROR_404], messages=[('error', _('You are not allowed to modify this shout.'))])
        return ValidationResult(False, errors=[RESPONSE_RESULT_ERROR_NOT_LOGGED_IN], messages=[('error', _('You are not signed in.'))])
    else:
        return result


def edit_shout_validator(request, id=None):
    result = modify_shout_validator(request, id)
    if result.valid:
        result = form_validator(request, ShoutForm)
        return result
    else:
        return result


def delete_message_validator(request):
    id = request.GET[u'id']
    id = Base62ToInt(id)

    result = object_exists_validator(message_controller.GetMessage, _('Message does not exist.'), id)
    if result.valid:
        if request.user.is_authenticated():
            return result
        return ValidationResult(False, errors=[RESPONSE_RESULT_ERROR_NOT_LOGGED_IN], messages=[('error', _('You are not signed in.'))])
    else:
        return result


def delete_conversation_validator(request):
    conversation_id = Base62ToInt(request.GET.get('id', '0'))

    result = object_exists_validator(message_controller.get_conversation, _('Conversation does not exist.'), conversation_id)
    if result.valid:
        if request.user.is_authenticated():
            return result
        return ValidationResult(False, errors=[RESPONSE_RESULT_ERROR_NOT_LOGGED_IN], messages=[('error', _('You are not signed in.'))])
    else:
        return result


def user_profile_validator(request, username, *args, **kwargs):
    if username == '@me' and request.user.is_authenticated():
        username = request.user.username
    elif username == '@me':
        return ValidationResult(False, messages=[('error', _('You are not signed in.'))], errors=[RESPONSE_RESULT_ERROR_NOT_LOGGED_IN])
    user = user_controller.GetUser(username)
    if user is not None:
        if not user.User.is_active and user.User != request.user and not request.user.is_staff:
            return ValidationResult(False, messages=[('error', _('User %(username)s is not active yet.') % {'username': username})], errors=[RESPONSE_RESULT_ERROR_NOT_ACTIVATED])
    return object_exists_validator(user_controller.GetUser, _('User %(username)s does not exist.') % {'username': username}, username)


def activate_api_validator(request, token, *args, **kwargs):
    if not token:
        return ValidationResult(False, {'token': [_('This field is required.')]}, [RESPONSE_RESULT_ERROR_BAD_REQUEST], [('error', _('You have entered some invalid input.'))])
    t = ConfirmToken.getToken(token, False, False)
    if not t:
        return ValidationResult(False, {'token': [_('Invalid activation token.')]}, [RESPONSE_RESULT_ERROR_BAD_REQUEST], [('error', _('You have entered some invalid input.'))])
    return form_validator(request, ExtenedSignUp, initial={'email': request.user.email, 'tokentype' : TOKEN_TYPE_API_EMAIL.value})


def shout_owner_view_validator(request, shout_id):
    if request.user.is_authenticated():
        result = object_exists_validator(shout_controller.GetPost, _('Shout does not exist.'), shout_id, True, True)
    else:
        result = object_exists_validator(shout_controller.GetPost, _('Shout does not exist.'), shout_id)
    if result.valid:
        shout = shout_controller.GetPost(shout_id, True, True)
        if shout.is_expired():
            if shout.OwnerUser != request.user and not request.user.is_staff:
                return ValidationResult(False, messages=[('error', _('Shout does not exist.'))],
                                        errors=[RESPONSE_RESULT_ERROR_404])
    return result

#def post_experience_validator(request,business_name,*args,**kwargs):
#	result = form_validator(request, ExperienceForm)
#	if result.valid:
#		business = business_controller.GetBusiness(business_name)
#		if not business:
#			return ValidationResult(False, messages=[('error', _('Business dose not exist.'))],)
#	return result


def share_experience_validator(request, exp_id, *args, **kwargs):
    result = object_exists_validator(shout_controller.GetPost,_('Experience dose not exist.'), Base62ToInt(exp_id))
    if result.valid:
        experience = experience_controller.GetExperience(request.user, Base62ToInt(exp_id),detailed = True)
        if not experience.canShare:
            return ValidationResult(False, messages=[('error', _('You can not share this experience.'))])
    return result


def experience_validator(request, *args, **kwargs):
    exp_frm = form_validator(request, ExperienceForm, initial=kwargs.has_key('initial') and kwargs['initial'] or {})
    if not args and (not kwargs.has_key('username') or not kwargs['username']):
        extended_exp_frm = form_validator(request, CreateTinyBusinessForm, initial=kwargs.has_key('initial') and kwargs['initial'] or {})
        exp_frm.form_errors.update(extended_exp_frm.form_errors)
        exp_frm.valid = exp_frm.valid and extended_exp_frm.valid
        exp_frm.messages = exp_frm.messages if exp_frm.messages else extended_exp_frm.messages
    return ValidationResult(exp_frm.valid, messages=exp_frm.messages, form_errors=exp_frm.form_errors)


def edit_experience_validator(request, exp_id, *args, **kwargs):
    result = object_exists_validator(shout_controller.GetPost,_('Experience dose not exist.'), Base62ToInt(exp_id))
    if result.valid:
        experience = experience_controller.GetExperience(request.user, Base62ToInt(exp_id),detailed=True)
        if not experience.canEdit:
            return ValidationResult(False, messages=[('error', _('You can not edit this experience.'))])
    return result


def delete_gallery_item_validator(request, item_id, *args, **kwargs):
    result = object_exists_validator(GalleryItem.objects.filter, _('Gallery Item dose not exist.'),Item = Item.objects.get(pk = Base62ToInt(item_id)), IsDisable = False)
    if result.valid:
        gallery_item = GalleryItem.objects.filter(Item = Item.objects.get(pk = Base62ToInt(item_id)), IsDisable = False)[0]
        try:
            #			galleries = request.user.Business.Galleries.all()
            galleries = business_controller.GetBusiness('business').Galleries.all()
            gallery = galleries[0] if galleries else None
            if not gallery_item.Gallery == gallery:
                ValidationResult(False, messages=[('error', _('You do not have permission to delete this item'))])
        except ValueError, e:
            return ValidationResult(False, messages=[('error', _('You do not have permission to delete this item'))])
    return result


def add_gallery_item_validator(request, business_name, *args, **kwargs):
    result = form_validator(request, ItemForm)
    if result.valid:
        business = business_controller.GetBusiness(business_name)
        business_galleries = business.Galleries.all()
        gallery = business_galleries[0] if business_galleries else None
        try:
            if request.user.Business != business:
                return ValidationResult(False, messages=[('error', _('You do not have permission to add item.'))],)
        except :
            return ValidationResult(False, messages=[('error', _('You do not have permission to add item.'))],)

        if not gallery:
            return ValidationResult(False, messages=[('error', _('Gallery does not exist.'))],)
    return result


def comment_on_post_validator(request, post_id, form_class):
    result = form_validator(request,CommentForm)
    if result.valid:
        result = object_exists_validator(shout_controller.GetPost,_('Experience dose not exist.'), Base62ToInt(post_id))
    return result


def delete_comment_validator(request, comment_id):
    result = object_exists_validator(comment_controller.GetCommentByID,_('Comment dose not exist.'), Base62ToInt(comment_id))
    if result.valid:
        comment = comment_controller.GetCommentByID(Base62ToInt(comment_id))
        if comment.OwnerUser != request.user:
            return ValidationResult(False, messages=[('error', _('You do not have permission to delete this comment'))])
    return result


def delete_event_validator(request, event_id):
    result = object_exists_validator(event_controller.GetEventByID,_('Activity dose not exist.'), Base62ToInt(event_id))
    if result.valid:
        event = event_controller.GetEventByID(Base62ToInt(event_id))
        if event.OwnerUser != request.user:
            return ValidationResult(False, messages=[('error', _('You do not have permission to delete this activity'))])
    return result