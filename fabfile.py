from __future__ import unicode_literals, with_statement

from fabric.api import *
from fabric.contrib.console import confirm
from contextlib import contextmanager as _contextmanager
from fabric.contrib import django

env.hosts = ['shoutit_local_api']
env.user = 'deploy'
env.keyfile = ['$HOME/.ssh/deploy_rsa']
env.directory = '/Volumes/MAC2/dev/shoutit_api_local'
env.activate = 'source /Volumes/MAC2/dev/shoutit_api_local/bin/activate'


@_contextmanager
def virtualenv():
    with cd(env.directory):
        with prefix(env.activate):
            yield


def test():
    local('python src/manage.py test')
    # with settings(warn_only=True):
    #     result = local('python src/manage.py test', capture=True)
    # if result.failed and not confirm("Tests failed. Continue anyway?"):
    #     abort("Aborting at user request.")


def commit():
    local("git add -p && git commit")


def push():
    local("git push")


def prepare_deploy():
    test()
    # commit()
    # push()


def run():
    with virtualenv():
        local('ls')
        django.settings_module('shoutit.settings')
        from django.conf import settings
        print(settings.LOCATION_ATTRIBUTES)

        # prepare_deploy()


def hello():
    print("Hello world!")
