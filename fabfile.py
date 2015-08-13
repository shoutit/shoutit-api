from __future__ import unicode_literals, with_statement

from fabric.api import *
from fabric.contrib.console import confirm

env.user = 'root'
env.use_ssh_config = True
env.roledefs = {
    'local': ['localhost'],
    'dev': ['root@dev.api.shoutit.com'],
    'prod': ['root@node-01.api.shoutit.com']
}


def test():
    with settings(warn_only=True):
        result = local('python src/manage.py test', capture=True)
    if result.failed and not confirm("Tests failed. Continue anyway?"):
        abort("Aborting at user request.")


def commit():
    local("git add -p && git commit")


def push():
    local("git push")


def pull(env_name):
    with cd('/opt/shoutit_api_{}/api'.format(env_name)):
        if confirm('Fast deploy [pull then restart]?'):
            out = run('git pull')
            if out != 'Already up-to-date.':
                run('supervisorctl restart all')
            return
        run('supervisorctl stop all')
        run('git pull')
        if confirm("Update requirements?"):
            run('/opt/shoutit_api_{}/bin/pip install    -r src/requirements/common_noupdate.txt'.format(env_name))
            run('/opt/shoutit_api_{0}/bin/pip install -U -r src/requirements/{0}.txt'.format(env_name))
        # run('/opt/shoutit_api_{}/bin/python src/manage.py test'.format(env))
        if confirm("Migratey?"):
            run('/opt/shoutit_api_{}/bin/python src/manage.py migrate'.format(env_name))
        if confirm("Clear all logs?"):
            run("find /opt/shoutit_api_{}/log/. -type f -exec cp /dev/null {{}} \;".format(env_name))
        run('chown shoutit_api_{0} -R /opt/shoutit_api_{0}/'.format(env_name))
        run('supervisorctl start all')


def prepare_deploy():
    test()
    # commit()
    # push()


def deploy():
    # with virtualenv():
    #     prepare_deploy()
    # with virtualenv():
    if 'dev' in env.roles:
        pull('dev')
    elif 'prod' in env.roles:
        pull('prod')
    else:
        print(':)')

