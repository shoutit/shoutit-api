from django.core.exceptions import ObjectDoesNotExist
# from django.core.files.base import ContentFile
#from django.db.models.query_utils import Q
#from activity_logger.logger import Logger
from common.constants import *


def PostExperience(user, state, text, businessProfile):
    exp = Experience(State=state, Text=text, AboutBusiness=businessProfile, OwnerUser=user, Type=int(POST_TYPE_EXPERIENCE))
    exp.save()
    businessProfile.Stream.PublishShout(exp)
    businessProfile.stream2.add_post(exp)
    user.profile.Stream.PublishShout(exp)
    user.profile.stream2.add_post(exp)
    event_controller.register_event(user, EVENT_TYPE_EXPERIENCE, exp)
    notifications_controller.notify_business_of_exp_posted(businessProfile.user, exp)
    realtime_controller.BindUserToPost(user, exp)
    return exp


def ShareExperience(user, exp_id):
    experience = shout_controller.get_post(exp_id)
    if experience:
        shared = SharedExperience(Experience=experience, OwnerUser=user)
        shared.save()
        event_controller.register_event(user, EVENT_TYPE_SHARE_EXPERIENCE, shared)
        notifications_controller.notify_user_of_exp_shared(experience.OwnerUser, shared)
        return shared
    else:
        raise ObjectDoesNotExist()


def EditExperience(exp_id, state, text):
    experience = shout_controller.get_post(exp_id)
    experience.State = state
    experience.Text = text
    experience.save()
    return experience


def GetUsersSharedExperience(exp_id):
    experience_sharedExperiences = SharedExperience.objects.filter(Experience__pk=exp_id).select_related('Experience', 'OwnerUser',
                                                                                                         'OwnerUser__Profile')
    return [sharedExperience.OwnerUser for sharedExperience in experience_sharedExperiences]


def GetExperience(exp_id, user, detailed=False):
    experience = Experience.objects.get_valid_experiences().filter(pk=exp_id).select_related('AboutBusiness', 'AboutBusiness__Profile',
                                                                                           'OwnerUser', 'OwnerUser__Profile').order_by(
        '-DatePublished')
    if experience:
        experience = experience[0]
        experience.detailed = detailed
        if detailed:
            sharedExperiences = SharedExperience.objects.filter(Experience__pk=exp_id).select_related('Experience', 'OwnerUser',
                                                                                                      'OwnerUser__Profile')
            comments = Comment.objects.filter(AboutPost__pk=exp_id).select_related('AboutPost', 'OwnerUser', 'OwnerUser__Profile')
            getDetailedExperience(user, experience, sharedExperiences, comments)
        return experience
    else:
        return None


def GetExperiences(user, owner_user=None, about_business=None, start_index=None, end_index=None, detailed=False, city=None):
    experiences_posts = Post.objects.filter(Type=POST_TYPE_EXPERIENCE)
    if owner_user:
        experiences_posts = experiences_posts.filter(OwnerUser=owner_user)
    if about_business:
        experiences_posts = experiences_posts.filter(experience__AboutBusiness=about_business)
    if city:
        experiences_posts = experiences_posts.filter(experience__AboutBusiness__City=city)
    experiences_post_ids = experiences_posts.values('pk')

    experiences = Experience.objects.get_valid_experiences().filter(pk__in=experiences_post_ids).select_related('AboutBusiness',
                                                                                                              'AboutBusiness__Profile',
                                                                                                              'OwnerUser',
                                                                                                              'OwnerUser__Profile').order_by(
        '-DatePublished')[start_index:end_index]
    sharedExperiences = SharedExperience.objects.filter(Experience__pk__in=experiences_post_ids).select_related('Experience', 'OwnerUser',
                                                                                                                'OwnerUser__Profile')
    comments = Comment.objects.filter(AboutPost__pk__in=experiences_post_ids).select_related('AboutPost', 'OwnerUser', 'OwnerUser__Profile')

    for experience in experiences:
        experience.detailed = detailed
        if detailed:
            getDetailedExperience(user, experience, sharedExperiences, comments)
    return experiences


def GetBusinessThumbsCount(business):
    ups = Experience.objects.filter(AboutBusiness=business, State=EXPERIENCE_UP.value).values('OwnerUser').distinct().count()
    downs = Experience.objects.filter(AboutBusiness=business, State=EXPERIENCE_DOWN.value).values('OwnerUser').distinct().count()
    return {
    'ups': ups,
    'downs': downs
    }


def GetExperiencesCount(profile):
    if profile and isinstance(profile, Profile):
        return profile.Stream.Posts.filter(Type=POST_TYPE_EXPERIENCE).count()
    elif profile and isinstance(profile, Business):
        return Post.objects.filter(Type=POST_TYPE_EXPERIENCE, experience__AboutBusiness=profile).count()


def getDetailedExperience(user, experience, sharedExperiences, comments):
    experience.usersSharedExperience = [sharedExperience.OwnerUser for sharedExperience in sharedExperiences if
                                        sharedExperience.Experience.pk == experience.pk]
    experience.comments = [comment for comment in comments if comment.AboutPost.pk == experience.pk and not comment.IsDisabled]

    experience.sharedExpsCount = len(experience.usersSharedExperience)
    experience.commentsCount = len(experience.comments)
    experience.canShare = user != experience.OwnerUser and user != experience.AboutBusiness.user and user not in experience.usersSharedExperience
    experience.canEdit = user == experience.OwnerUser and not experience.sharedExpsCount and not experience.commentsCount
    experience.isOwner = True if experience.OwnerUser == user else False


from shoutit.controllers import event_controller, shout_controller, notifications_controller, \
    realtime_controller
from shoutit.models import Experience, Post, Business, SharedExperience, Comment, Profile