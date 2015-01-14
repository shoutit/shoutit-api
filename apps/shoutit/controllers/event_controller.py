from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q

from common.constants import DEFAULT_PAGE_SIZE, POST_TYPE_EVENT, EVENT_TYPE_FOLLOW_USER, EVENT_TYPE_FOLLOW_TAG, \
    EVENT_TYPE_SHOUT_REQUEST, EVENT_TYPE_EXPERIENCE, EVENT_TYPE_SHARE_EXPERIENCE, EVENT_TYPE_SHOUT_OFFER, EVENT_TYPE_POST_DEAL, \
    EVENT_TYPE_BUY_DEAL, EVENT_TYPE_COMMENT, EVENT_TYPE_FOLLOW_BUSINESS
from apps.shoutit.models import Event, Tag, Trade, Experience, Deal, Comment, Profile, Business, SharedExperience


def RegisterEvent(user, type, attached_object=None):
    from apps.shoutit.controllers.user_controller import get_profile

    pk = attached_object and attached_object.pk or None
    ct = attached_object and ContentType.objects.db_manager(attached_object._state.db).get_for_model(attached_object) or None
    event = Event(OwnerUser=user, Type=POST_TYPE_EVENT, EventType=type, object_id=pk, content_type=ct)
    event.save()

    profile = get_profile(user.username)
    profile.Stream.PublishShout(event)
    profile.stream2.add_post(event)


# realtime_message = realtime_controller.WrapRealtimeMessage(render_event(event),RealtimeType.values[REALTIME_TYPE_EVENT])
#	realtime_controller.BroadcastRealtimeMessage(realtime_message,user_controller.GetProfile(user).City)

def GetUserEvents(user, start_index=None, end_index=None):
    return Event.objects.get_valid_events().filter(OwnerUser=user)


def GetPublicEventsByLocation(country=None, city=None, date=None):
    events = []
    #	Q(event__EventType = EVENT_TYPE_FOLLOW_USER ) |
    events = Event.objects.filter(IsDisabled=False)
    events = events.filter(~Q(OwnerUser__first_name=""))

    #	events = events.filter(Q(EventType = EVENT_TYPE_FOLLOW_TAG ) | Q(EventType = EVENT_TYPE_SHARE_EXPERIENCE ) | Q(EventType = EVENT_TYPE_COMMENT ) | Q(EventType = EVENT_TYPE_SHOUT_OFFER) | Q(EventType = EVENT_TYPE_SHOUT_REQUEST ) | Q(EventType = EVENT_TYPE_FOLLOW_BUSINESS )  )
    events = events.filter(
        Q(EventType=EVENT_TYPE_FOLLOW_TAG) | Q(EventType=EVENT_TYPE_EXPERIENCE) | Q(EventType=EVENT_TYPE_SHARE_EXPERIENCE) | Q(
            EventType=EVENT_TYPE_COMMENT) | Q(EventType=EVENT_TYPE_SHOUT_OFFER) | Q(EventType=EVENT_TYPE_SHOUT_REQUEST) | Q(
            EventType=EVENT_TYPE_FOLLOW_BUSINESS))

    if country:
        events = events.filter(Q(OwnerUser__profile__Country=country) | Q(OwnerUser__business__Country=country))

    if city:
        events = events.filter(Q(OwnerUser__profile__City=city) | Q(OwnerUser__business__City=city))

    #	extra_ids = Experience.objects.filter(AboutBusiness__City = city).values('pk')
    #	ct = ContentType.objects.get_for_model(Experience)
    #	extra_events = Event.objects.filter( object_id__in=extra_ids)
    #	extra_events += events
    if date:
        events = events.filter(DatePublished__gte=date).order_by('-DatePublished').select_related('OwnerUser', 'OwnerUser__Profile',
                                                                                                  'OwnerUser__Business', 'attached_object')
    else:
        events = events.order_by('-DatePublished')[0:DEFAULT_PAGE_SIZE].select_related('OwnerUser', 'OwnerUser__Profile',
                                                                                       'OwnerUser__Business', 'attached_object')
    return events


def DeleteEventAboutObj(attached_object):
    event = Event.objects.get(content_type__name=attached_object._meta.module_name, object_id=attached_object.pk)
    if event:
        event.IsDisabled = True
        event.save()


def DeleteEvent(event_id):
    event = Event.objects.get(pk=event_id)
    if event:
        event.IsDisabled = True
        event.save()


def GetEventByID(event_id):
    event = Event.objects.get(pk=event_id)
    return event if event else None


#def MuteEvent(event_id):
#	event = Event.objects.get(pk = event_id)
#	if event:
#		event.IsMuted = True
#		event.save()

def GetDetailedEvents(events):
    from apps.shoutit.controllers.shout_controller import get_trade_images

    related_ids = {'user_ids': [], 'business_ids': [], 'tag_ids': [], 'trade_ids': [], 'experience_ids': [], 'shared_exp_ids': [],
                   'comment_ids': [], 'deal_ids': []}
    for event in events:
        if event.EventType == EVENT_TYPE_FOLLOW_USER:
            related_ids['user_ids'].append(event.object_id)
        elif event.EventType == EVENT_TYPE_FOLLOW_BUSINESS:
            related_ids['business_ids'].append(event.object_id)
        elif event.EventType == EVENT_TYPE_FOLLOW_TAG:
            related_ids['tag_ids'].append(event.object_id)
        elif event.EventType == EVENT_TYPE_SHOUT_OFFER or event.EventType == EVENT_TYPE_SHOUT_REQUEST:
            related_ids['trade_ids'].append(event.object_id)
        elif event.EventType == EVENT_TYPE_EXPERIENCE:
            related_ids['experience_ids'].append(event.object_id)
        elif event.EventType == EVENT_TYPE_SHARE_EXPERIENCE:
            related_ids['shared_exp_ids'].append(event.object_id)
        elif event.EventType == EVENT_TYPE_COMMENT:
            related_ids['comment_ids'].append(event.object_id)
        elif event.EventType == EVENT_TYPE_POST_DEAL or event.EventType == EVENT_TYPE_BUY_DEAL:
            related_ids['deal_ids'].append(event.object_id)

    related = {'users': [], 'businesses': [], 'tags': [], 'trades': [], 'experiences': [], 'shared_exps': [], 'comments': [], 'deals': []}
    if related_ids['user_ids']:
        related['users'] = list(Profile.objects.filter(pk__in=related_ids['user_ids']).select_related('User'))
    if related_ids['business_ids']:
        related['businesses'] = list(Business.objects.filter(pk__in=related_ids['user_ids']).select_related('User'))
    if related_ids['tag_ids']:
        related['tags'] = list(Tag.objects.filter(pk__in=related_ids['tag_ids']))
    if related_ids['trade_ids']:
        trades = Trade.objects.filter(pk__in=related_ids['trade_ids']).select_related('OwnerUser', 'OwnerUser__Profile',
                                                                                      'OwnerUser__Business', 'Item', 'Item__Currency')
        trades = get_trade_images(trades)
        related['trades'] = list(trades)
    if related_ids['experience_ids']:
        related['experiences'] = list(
            Experience.objects.filter(pk__in=related_ids['experience_ids']).select_related('OwnerUser', 'OwnerUser__Profile',
                                                                                           'AboutBusiness__User'))
    if related_ids['shared_exp_ids']:
        related['shared_exps'] = list(
            SharedExperience.objects.filter(pk__in=related_ids['shared_exp_ids']).select_related('OwnerUser', 'OwnerUser__Profile',
                                                                                                 'Experience', 'Experience__AboutBusiness',
                                                                                                 'Experience__AboutBusiness__User'))
    if related_ids['comment_ids']:
        related['comments'] = list(
            Comment.objects.filter(pk__in=related_ids['comment_ids']).select_related('OwnerUser', 'OwnerUser__Profile',
                                                                                     'OwnerUser__Business', 'AboutPost'))
    if related_ids['deal_ids']:
        related['deals'] = list(
            Deal.objects.filter(pk__in=related_ids['deal_ids']).select_related('OwnerUser', 'OwnerUser__Business', 'Item',
                                                                               'Item__Currency'))

    for event in events:
        if event.EventType == EVENT_TYPE_FOLLOW_USER:
            for user in related['users']:
                if user.pk == event.object_id:
                    event.attached_object = user
                    #					related['users'].remove(user)
                    break
        elif event.EventType == EVENT_TYPE_FOLLOW_BUSINESS:
            for business in related['businesses']:
                if business.pk == event.object_id:
                    event.attached_object = business
                    #					related['users'].remove(user)
                    break
        elif event.EventType == EVENT_TYPE_FOLLOW_TAG:
            for tag in related['tags']:
                if tag.pk == event.object_id:
                    event.attached_object = tag
                    #					related['tags'].remove(tag)
                    break
        elif event.EventType == EVENT_TYPE_SHOUT_OFFER or event.EventType == EVENT_TYPE_SHOUT_REQUEST:
            for trade in related['trades']:
                if trade.pk == event.object_id:
                    event.attached_object = trade
                    #					related['trades'].remove(trade)
                    break
        elif event.EventType == EVENT_TYPE_EXPERIENCE:
            for experience in related['experiences']:
                if experience.pk == event.object_id:
                    event.attached_object = experience
                    #					related['experiences'].remove(experience)
                    break
        elif event.EventType == EVENT_TYPE_SHARE_EXPERIENCE:
            for shared in related['shared_exps']:
                if shared.pk == event.object_id:
                    event.attached_object = shared
                    #					related['experiences'].remove(experience)
                    break
        elif event.EventType == EVENT_TYPE_COMMENT:
            for comment in related['comments']:
                if comment.pk == event.object_id:
                    event.attached_object = comment
                    #					related['comments'].remove(comment)
                    break
        elif event.EventType == EVENT_TYPE_POST_DEAL or event.EventType == EVENT_TYPE_BUY_DEAL:
            for deal in related['deals']:
                if deal.pk == event.object_id:
                    event.attached_object = deal
                    #					related['deals'].remove(deal)
                    break
    return events
