
from django.contrib.contenttypes.models import ContentType
from django.db.models.query_utils import Q
from apps.shoutit.constants import DEFAULT_PAGE_SIZE, POST_TYPE_EVENT, RealtimeType, REALTIME_TYPE_EVENT, EVENT_TYPE_FOLLOW_USER, EVENT_TYPE_FOLLOW_TAG, EVENT_TYPE_SHOUT_REQUEST, EVENT_TYPE_EXPERIENCE, EVENT_TYPE_SHARE_EXPERIENCE, EVENT_TYPE_SHOUT_OFFER, EVENT_TYPE_POST_DEAL, EVENT_TYPE_BUY_DEAL, EVENT_TYPE_GALLERY_ITEM, EVENT_TYPE_COMMENT, EVENT_TYPE_FOLLOW_BUSINESS
from apps.shoutit.utils import IntToBase62
from apps.shoutit.api.renderers import render_event


def RegisterEvent(user, type, attached_object=None):
	pk = attached_object and attached_object.pk or None
	ct = attached_object and ContentType.objects.db_manager(attached_object._state.db).get_for_model(attached_object) or None
	event = Event(OwnerUser = user,Type = POST_TYPE_EVENT, EventType = type, object_pk = pk, content_type=ct)
	event.save()

	profile = apps.shoutit.controllers.user_controller.GetUser(user.username)
	profile.Stream.PublishShout(event)
#	realtime_message = realtime_controller.WrapRealtimeMessage(render_event(event),RealtimeType.values[REALTIME_TYPE_EVENT])
#	realtime_controller.BroadcastRealtimeMessage(realtime_message,user_controller.GetProfile(user).City)

def GetUserEvents(user, start_index=None, end_index=None):
	return Event.objects.GetValidEvents().filter(OwnerUser = user)

def GetPublicEventsByLocation(country=None,city=None,date = None):
	events = []
#	Q(event__EventType = EVENT_TYPE_FOLLOW_USER ) |
	events = Event.objects.filter(IsDisabled = False)
	events = events.filter(~Q(OwnerUser__first_name = ""))

#	events = events.filter(Q(EventType = EVENT_TYPE_FOLLOW_TAG ) | Q(EventType = EVENT_TYPE_SHARE_EXPERIENCE ) | Q(EventType = EVENT_TYPE_COMMENT ) | Q(EventType = EVENT_TYPE_SHOUT_OFFER) | Q(EventType = EVENT_TYPE_SHOUT_REQUEST ) | Q(EventType = EVENT_TYPE_FOLLOW_BUSINESS )  )
	events = events.filter(Q(EventType = EVENT_TYPE_FOLLOW_TAG ) | Q(EventType = EVENT_TYPE_EXPERIENCE ) | Q(EventType = EVENT_TYPE_SHARE_EXPERIENCE ) | Q(EventType = EVENT_TYPE_COMMENT ) | Q(EventType = EVENT_TYPE_SHOUT_OFFER) | Q(EventType = EVENT_TYPE_SHOUT_REQUEST ) | Q(EventType = EVENT_TYPE_FOLLOW_BUSINESS )  )

	if country:
		events = events.filter(Q(OwnerUser__Profile__Country = country)|Q(OwnerUser__Business__Country = country))

	if city:
		events = events.filter(Q(OwnerUser__Profile__City = city)|Q(OwnerUser__Business__City = city))

#	extra_ids = Experience.objects.filter(AboutBusiness__City = city).values('id')
#	ct = ContentType.objects.get_for_model(Experience)
#	extra_events = Event.objects.filter( object_pk__in=extra_ids)
#	extra_events += events
	if date:
		events = events.filter(DatePublished__gte = date).order_by('-DatePublished').select_related('OwnerUser','OwnerUser__Profile','OwnerUser__Business','AttachedObject')
	else:
		events = events.order_by('-DatePublished')[0:DEFAULT_PAGE_SIZE].select_related('OwnerUser','OwnerUser__Profile','OwnerUser__Business','AttachedObject')
	return events


def DeleteEventAboutObj(AttachedObject):
	event = Event.objects.get(content_type__name = AttachedObject._meta.module_name, object_pk = AttachedObject.id)
	if event:
		event.IsDisabled = True
		event.save()

def DeleteEvent(event_id):
	event = Event.objects.get(pk = event_id)
	if event:
		event.IsDisabled = True
		event.save()

def GetEventByID(event_id):
	event = Event.objects.get(pk = event_id)
	return event if event else None

#def MuteEvent(event_id):
#	event = Event.objects.get(pk = event_id)
#	if event:
#		event.IsMuted = True
#		event.save()

def GetDetailedEvents(events):
	related_ids = {'user_ids' : [],'business_ids' : [], 'tag_ids' : [], 'trade_ids' : [], 'experience_ids' : [], 'shared_exp_ids' : [], 'comment_ids' : [], 'deal_ids' : [] }
	for event in events:
		if event.EventType == EVENT_TYPE_FOLLOW_USER:
			related_ids['user_ids'].append(event.object_pk)
		elif event.EventType == EVENT_TYPE_FOLLOW_BUSINESS:
			related_ids['business_ids'].append(event.object_pk)
		elif event.EventType == EVENT_TYPE_FOLLOW_TAG:
			related_ids['tag_ids'].append(event.object_pk)
		elif event.EventType == EVENT_TYPE_SHOUT_OFFER or event.EventType == EVENT_TYPE_SHOUT_REQUEST:
			related_ids['trade_ids'].append(event.object_pk)
		elif event.EventType == EVENT_TYPE_EXPERIENCE:
			related_ids['experience_ids'].append(event.object_pk)
		elif event.EventType == EVENT_TYPE_SHARE_EXPERIENCE:
			related_ids['shared_exp_ids'].append(event.object_pk)
		elif event.EventType == EVENT_TYPE_COMMENT:
			related_ids['comment_ids'].append(event.object_pk)
		elif event.EventType == EVENT_TYPE_POST_DEAL or event.EventType == EVENT_TYPE_BUY_DEAL:
			related_ids['deal_ids'].append(event.object_pk)

	related = {'users' : [],'businesses' : [], 'tags' : [], 'trades' : [], 'experiences' : [], 'shared_exps' : [] , 'comments' : [], 'deals' : [] }
	if related_ids['user_ids']:
		related['users'] = list(UserProfile.objects.filter(pk__in = related_ids['user_ids']).select_related('User'))
	if related_ids['business_ids']:
		related['businesses'] = list(BusinessProfile.objects.filter(pk__in = related_ids['user_ids']).select_related('User'))
	if related_ids['tag_ids']:
		related['tags'] = list(Tag.objects.filter(pk__in = related_ids['tag_ids']))
	if related_ids['trade_ids']:
		trades = Trade.objects.filter(pk__in = related_ids['trade_ids']).select_related('OwnerUser','OwnerUser__Profile','OwnerUser__Business','Item','Item__Currency')
		trades = shout_controller.get_trade_images(trades)
		related['trades'] = list(trades)
	if related_ids['experience_ids']:
		related['experiences'] = list(Experience.objects.filter(pk__in = related_ids['experience_ids']).select_related('OwnerUser','OwnerUser__Profile','AboutBusiness__User'))
	if related_ids['shared_exp_ids']:
		related['shared_exps'] = list(SharedExperience.objects.filter(pk__in = related_ids['shared_exp_ids']).select_related('OwnerUser','OwnerUser__Profile','Experience','Experience__AboutBusiness','Experience__AboutBusiness__User'))
	if related_ids['comment_ids']:
		related['comments'] = list(Comment.objects.filter(pk__in = related_ids['comment_ids']).select_related('OwnerUser','OwnerUser__Profile','OwnerUser__Business','AboutPost'))
	if related_ids['deal_ids']:
		related['deals'] = list(Deal.objects.filter(pk__in = related_ids['deal_ids']).select_related('OwnerUser','OwnerUser__Business','Item','Item__Currency'))

	for event in events:
		if event.EventType == EVENT_TYPE_FOLLOW_USER:
			for user in related['users']:
				if user.pk == int(event.object_pk):
					event.AttachedObject = user
#					related['users'].remove(user)
					break
		elif event.EventType == EVENT_TYPE_FOLLOW_BUSINESS:
			for business in related['businesses']:
				if business.pk == int(event.object_pk):
					event.AttachedObject = business
#					related['users'].remove(user)
					break
		elif event.EventType == EVENT_TYPE_FOLLOW_TAG:
			for tag in related['tags']:
				if tag.pk == int(event.object_pk):
					event.AttachedObject = tag
#					related['tags'].remove(tag)
					break
		elif event.EventType == EVENT_TYPE_SHOUT_OFFER or event.EventType == EVENT_TYPE_SHOUT_REQUEST:
			for trade in related['trades']:
				if trade.pk == int(event.object_pk):
					event.AttachedObject = trade
#					related['trades'].remove(trade)
					break
		elif event.EventType == EVENT_TYPE_EXPERIENCE:
			for experience in related['experiences']:
				if experience.pk == int(event.object_pk):
					event.AttachedObject = experience
#					related['experiences'].remove(experience)
					break
		elif event.EventType == EVENT_TYPE_SHARE_EXPERIENCE:
			for shared in related['shared_exps']:
				if shared.pk == int(event.object_pk):
					event.AttachedObject = shared
#					related['experiences'].remove(experience)
					break
		elif event.EventType == EVENT_TYPE_COMMENT:
			for comment in related['comments']:
				if comment.pk == int(event.object_pk):
					event.AttachedObject = comment
#					related['comments'].remove(comment)
					break
		elif event.EventType == EVENT_TYPE_POST_DEAL or event.EventType == EVENT_TYPE_BUY_DEAL:
			for deal in related['deals']:
				if deal.pk == int(event.object_pk):
					event.AttachedObject = deal
#					related['deals'].remove(deal)
					break
	return events



from apps.shoutit.models import Event,Tag,Trade,Experience,Deal,Comment,UserProfile,BusinessProfile, SharedExperience
import apps.shoutit.controllers.user_controller,realtime_controller,user_controller,shout_controller