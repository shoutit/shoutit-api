from django.core.exceptions import ObjectDoesNotExist
# from django.core.files.base import ContentFile
# from django.db.models.query_utils import Q
from common.constants import *


def PostExperience(user, state, text, businessProfile):
    exp = Experience(State=state, text=text, AboutBusiness=businessProfile, user=user, type=int(POST_TYPE_EXPERIENCE))
    exp.save()
    businessProfile.stream.add_post(exp)
    user.profile.stream.add_post(exp)
    event_controller.register_event(user, EVENT_TYPE_EXPERIENCE, exp)
    notifications_controller.notify_business_of_exp_posted(businessProfile.user, exp)
    return exp


def ShareExperience(user, exp_id):
    experience = shout_controller.get_post(exp_id)
    if experience:
        shared = SharedExperience(Experience=experience, user=user)
        shared.save()
        event_controller.register_event(user, EVENT_TYPE_SHARE_EXPERIENCE, shared)
        notifications_controller.notify_user_of_exp_shared(experience.user, shared)
        return shared
    else:
        raise ObjectDoesNotExist()


def EditExperience(exp_id, state, text):
    experience = shout_controller.get_post(exp_id)
    experience.State = state
    experience.text = text
    experience.save()
    return experience


def GetUsersSharedExperience(exp_id):
    experience_sharedExperiences = SharedExperience.objects.filter(Experience__pk=exp_id).select_related('Experience', 'user',
                                                                                                         'user__profile')
    return [sharedExperience.user for sharedExperience in experience_sharedExperiences]


def GetExperience(exp_id, user, detailed=False):
    experience = Experience.objects.get_valid_experiences().filter(pk=exp_id).select_related('AboutBusiness', 'user',
                                                                                             'user__profile').order_by(
        '-date_published')
    if experience:
        experience = experience[0]
        experience.detailed = detailed
        if detailed:
            sharedExperiences = SharedExperience.objects.filter(Experience__pk=exp_id).select_related('Experience', 'user', 'user__profile')
            comments = Comment.objects.filter(AboutPost__pk=exp_id).select_related('AboutPost', 'user', 'user__profile')
            getDetailedExperience(user, experience, sharedExperiences, comments)
        return experience
    else:
        return None


def GetExperiences(user, owner_user=None, about_business=None, start_index=None, end_index=None, detailed=False, city=None):
    experiences_posts = Post.objects.filter(type=POST_TYPE_EXPERIENCE)
    if owner_user:
        experiences_posts = experiences_posts.filter(user=owner_user)
    if about_business:
        experiences_posts = experiences_posts.filter(experience__AboutBusiness=about_business)
    if city:
        experiences_posts = experiences_posts.filter(experience__AboutBusiness__city=city)
    experiences_post_ids = experiences_posts.values('pk')

    experiences = Experience.objects.get_valid_experiences().filter(pk__in=experiences_post_ids).select_related('AboutBusiness', 'user',
                                                                                                                'user__profile').order_by(
        '-date_published')[start_index:end_index]
    sharedExperiences = SharedExperience.objects.filter(Experience__pk__in=experiences_post_ids).select_related('Experience', 'user',
                                                                                                                'user__profile')
    comments = Comment.objects.filter(AboutPost__pk__in=experiences_post_ids).select_related('AboutPost', 'user', 'user__profile')

    for experience in experiences:
        experience.detailed = detailed
        if detailed:
            getDetailedExperience(user, experience, sharedExperiences, comments)
    return experiences


def GetBusinessThumbsCount(business):
    ups = Experience.objects.filter(AboutBusiness=business, State=EXPERIENCE_UP.value).values('user').distinct().count()
    downs = Experience.objects.filter(AboutBusiness=business, State=EXPERIENCE_DOWN.value).values('user').distinct().count()
    return {
        'ups': ups,
        'downs': downs
    }


def GetExperiencesCount(profile):
    if profile and isinstance(profile, Profile):
        return profile.stream.posts.filter(type=POST_TYPE_EXPERIENCE).count()
    elif profile and isinstance(profile, Business):
        return Post.objects.filter(type=POST_TYPE_EXPERIENCE, experience__AboutBusiness=profile).count()


def getDetailedExperience(user, experience, sharedExperiences, comments):
    experience.usersSharedExperience = [sharedExperience.user for sharedExperience in sharedExperiences if
                                        sharedExperience.Experience.pk == experience.pk]
    experience.comments = [comment for comment in comments if comment.AboutPost.pk == experience.pk and not comment.is_disabled]

    experience.sharedExpsCount = len(experience.usersSharedExperience)
    experience.commentsCount = len(experience.comments)
    experience.canShare = user != experience.user and user != experience.AboutBusiness.user and user not in experience.usersSharedExperience
    experience.canEdit = user == experience.user and not experience.sharedExpsCount and not experience.commentsCount
    experience.isOwner = True if experience.user == user else False


from shoutit.controllers import event_controller, shout_controller, notifications_controller
from shoutit.models import Experience, Post, Business, SharedExperience, Comment, Profile