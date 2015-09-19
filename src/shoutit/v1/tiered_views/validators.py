from __future__ import unicode_literals
import uuid

from django.core.exceptions import ObjectDoesNotExist

from django.utils.translation import ugettext_lazy as _

from shoutit.models import Profile, Business
from shoutit.controllers import shout_controller, comment_controller, experience_controller
from shoutit.controllers.user_controller import get_profile
from shoutit.forms import BusinessEditProfileForm, CreateTinyBusinessForm
from shoutit.v1.tiered_views.tiers import ValidationResult as VR, RESPONSE_RESULT_ERROR_404


def uuid_validator(uuid_string):
    try:
        uuid.UUID(uuid_string)
        return VR(True)
    except Exception as e:
        print e
        return VR(False)


def object_exists_validator(function, using_uuid, error_message='object does not exist', *args,
                            **kwargs):
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


def form_validator(request, form_class, message='You have entered some invalid input.',
                   initial=None):
    initial = initial or {}
    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, initial=initial)
        if form.is_valid():
            return VR(True, data={'form': form})
        else:
            return VR(False, messages=[('error', _(message))], form_errors=form.errors)
    return VR(True)


def user_edit_profile_validator(request, username, email):
    result = object_exists_validator(get_profile, False, _('User %(username)s does not exist.') % {
        'username': username}, username)
    if result:
        profile = result.data
        if username == request.user.username or request.user.is_staff:
            init = {'username': username, 'email': email}
            if profile and isinstance(profile, Profile):
                result = form_validator(request, UserEditProfileForm, initial=init)
            elif profile and isinstance(profile, Business):
                result = form_validator(request, BusinessEditProfileForm, initial=init)
            else:
                result = VR(False, messages=[
                    ('error', _('User %(username)s does not exist.') % {'username': username})],
                            errors=[RESPONSE_RESULT_ERROR_404])
            return result
        else:
            return VR(False,
                      messages=[('error', _("You don't have permissions to edit this profile."))])
    return result


def share_experience_validator(request, exp_id, *args, **kwargs):
    result = object_exists_validator(shout_controller.get_post, True,
                                     _('Experience dose not exist.'), exp_id)
    if result:
        experience = experience_controller.GetExperience(exp_id, request.user, detailed=True)
        if not experience.canShare:
            return VR(False, messages=[('error', _('You can not share this experience.'))])
    return result


def experience_validator(request, *args, **kwargs):
    exp_frm = form_validator(request, ExperienceForm,
                             initial='initial' in kwargs and kwargs['initial'] or {})
    if not args and ('username' not in kwargs or not kwargs['username']):
        extended_exp_frm = form_validator(request, CreateTinyBusinessForm,
                                          initial='initial' in kwargs and kwargs['initial'] or {})
        exp_frm.form_errors.update(extended_exp_frm.form_errors)
        exp_frm.valid = exp_frm.valid and extended_exp_frm.valid
        exp_frm.messages = exp_frm.messages if exp_frm.messages else extended_exp_frm.messages
    return VR(exp_frm.valid, messages=exp_frm.messages, form_errors=exp_frm.form_errors)


def experience_view_validator(request, exp_id, *args, **kwargs):
    return object_exists_validator(experience_controller.GetExperience, True,
                                   _('Experience does not exist.'), exp_id, request.user, True)


def edit_experience_validator(request, exp_id, *args, **kwargs):
    result = object_exists_validator(shout_controller.get_post, True,
                                     _('Experience dose not exist.'), exp_id)
    if result.valid:
        experience = experience_controller.GetExperience(exp_id, request.user, detailed=True)
        if not experience.canEdit:
            return VR(False, messages=[('error', _('You can not edit this experience.'))])
    return result


def comment_on_post_validator(request, post_id, form_class):
    result = form_validator(request, CommentForm)
    if result:
        result = object_exists_validator(shout_controller.get_post, True,
                                         _('Experience dose not exist.'), post_id)
    return result


def delete_comment_validator(request, comment_id):
    result = object_exists_validator(comment_controller.GetCommentByID, True,
                                     _('Comment dose not exist.'), comment_id)
    if result:
        comment = comment_controller.GetCommentByID(comment_id)
        if comment.user != request.user:
            return VR(False,
                      messages=[('error', _('You do not have permission to delete this comment'))])
    return result
