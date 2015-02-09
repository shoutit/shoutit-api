# from activity_logger.models import Activity


class Logger(object):
    @staticmethod
    def log(request, activity=None, type=0, data={}):
        # todo: hack
        if True:
            return

        if not request:
            return

        if not hasattr(request, 'request_object'):
            return
        if activity is None:
            activity = Activity(type=type, request=request.request_object)
        else:
            activity.request = request.request_object
        activity.save()
        activity.add_data(data)