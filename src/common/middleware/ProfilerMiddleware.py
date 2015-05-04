import os
import re
import cProfile
import time

from django.conf import settings

words_re = re.compile(r'\s+')

group_prefix_re = [
    re.compile("^.*/django/[^/]+"),
    re.compile("^(.*)/[^/]+$"),  # extract module path
    re.compile(".*"),  # catch strange entries
]


class ProfileMiddleware(object):
    def process_request(self, request):
        if settings.DEBUG:
            self.prof = cProfile.Profile()

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG:
            self.statsfile = os.path.join(settings.PROFILE_LOG_BASE, '.'.join(
                [callback.__module__, callback.__name__,
                 time.strftime("%Y%m%dT%H%M%S", time.gmtime()), 'prof']))
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def get_group(self, file):
        for g in group_prefix_re:
            name = g.findall(file)
            if name:
                return name[0]

    def get_summary(self, results_dict, sum):
        list = [(item[1], item[0]) for item in results_dict.items()]
        list.sort(reverse=True)
        list = list[:40]

        res = "	  tottime\n"
        for item in list:
            res += "%4.1f%% %7.3f %s\n" % ( 100 * item[0] / sum if sum else 0, item[0], item[1] )

        return res

    def summary_for_files(self, stats_str):
        stats_str = stats_str.split("\n")[5:]

        mystats = {}
        mygroups = {}

        sum = 0

        for s in stats_str:
            fields = words_re.split(s)
            if len(fields) == 7:
                time = float(fields[2])
                sum += time
                file = fields[6].split(":")[0]
                if file not in mystats:
                    mystats[file] = 0
                mystats[file] += time
                group = self.get_group(file)
                if group not in mygroups:
                    mygroups[group] = 0
                mygroups[group] += time

        return "\n" + \
               " ---- By file ----\n\n" + self.get_summary(mystats, sum) + "\n" + \
               " ---- By group ---\n\n" + self.get_summary(mygroups, sum) + \
               "\n"

    def process_response(self, request, response):
        if settings.DEBUG:
            self.prof.dump_stats(self.statsfile)
        return response
