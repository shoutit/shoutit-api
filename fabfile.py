from __future__ import unicode_literals, with_statement

from fabric.api import *
from fabric.contrib.console import confirm

env.hosts = ['node-01.api.shoutit.com']
env.user = 'root'


def test():
    with settings(warn_only=True):
        result = local('python src/manage.py test', capture=True)
    if result.failed and not confirm("Tests failed. Continue anyway?"):
        abort("Aborting at user request.")


def commit():
    local("git add -p && git commit")


def push():
    local("git push")


def pull():
    with cd('/opt/shoutit_api_prod/api'):
        run('git pull')
        # run('/opt/shoutit_api_prod/bin/python src/manage.py test')
        run('/opt/shoutit_api_prod/bin/python src/manage.py migrate')
        run('/opt/shoutit_api_prod/bin/pip install -U -r src/requirements/prod.txt')
        run('supervisorctl restart all')


def prepare_deploy():
    test()
    # commit()
    # push()


def deploy_prod():
    # with virtualenv():
    #     prepare_deploy()
    # with virtualenv():
    pull()

