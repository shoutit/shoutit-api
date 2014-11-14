from django.contrib.contenttypes.models import ContentType


def CreateReport(user, text, attached_object=None):
    pk = attached_object and attached_object.pk or None
    ct = attached_object and ContentType.objects.db_manager(attached_object._state.db).get_for_model(attached_object) or None
    report = Report(user=user, Text=text, object_pk=pk, content_type=ct)
    report.save()


from apps.shoutit.models import Report