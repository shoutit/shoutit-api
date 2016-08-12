from __future__ import unicode_literals, with_statement

import os

from fabric.api import *
from fabric.contrib.console import confirm

SRC_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'src')

env.user = 'root'
env.use_ssh_config = True
env.roledefs = {
    'local': ['localhost'],
    'dev': ['root@dev.api.shoutit.com'],
    'prod': ['root@node-01.api.shoutit.com']
}
manage_py = os.path.join(SRC_DIR, 'manage.py')
# Todo: This works only on Windows (specifically my machine)
scripts_dir = os.path.join(os.path.dirname(os.path.dirname(SRC_DIR)), 'Scripts')
# if the "Scripts" dir does not exist, assume an environment where the commands can be run from the project source dir
if not os.path.exists(scripts_dir):
    scripts_dir = SRC_DIR


def local_flake8():
    print("Running flake8...")
    with lcd(scripts_dir):
        local('flake8 %s ' % SRC_DIR)


def local_radon():
    print("Running radon...")
    with lcd(scripts_dir):
        local('radon cc -s -n B %s ' % SRC_DIR)


def local_update():
    print("Updating local requirements...")
    with lcd(scripts_dir):
        local('pip install -U -r %s' % os.path.join(SRC_DIR, 'requirements', 'dev.txt'))
        local('pip install -r %s' % os.path.join(SRC_DIR, 'requirements', 'common_noupdate.txt'))


def preview_local_updates():
    print("Checking local requirements...")
    with lcd(scripts_dir):
        local('python pip-review --local')


def local_test():
    with lcd(scripts_dir):
        with settings(warn_only=True):
            result = local('python %s test --keepdb --verbosity=2' % manage_py)


def local_commit():
    local("git add -p && git commit")


def local_push(env_name):
    local("git push")


def remote_pull(env_short_name):
    remote_env = 'shoutit_api_%s' % env_short_name
    remote_env_dir = '/opt/%s/' % remote_env
    with cd('/opt/%s/api' % remote_env):
        if confirm('Fast deploy [pull then restart]?'):
            out = run('git pull')
            if out != 'Already up-to-date.':
                run('supervisorctl restart all')
            return
        run('supervisorctl stop all')
        run('git pull')
        if confirm("Update requirements?"):
            run('%sbin/pip install -r src/requirements/common_noupdate.txt' % remote_env_dir)
            run('%sbin/pip install -U -r src/requirements/%s.txt' % (remote_env_dir, env_short_name))
        # run('/opt/{}/bin/python src/manage.py test'.format(env))
        if confirm("Migrate?"):
            run('%sbin/python src/manage.py migrate --noinput' % remote_env_dir)
        if confirm("Clear all logs?"):
            run("find {}log/. -type f -exec cp /dev/null {{}} \;".format(remote_env_dir))
        run('chown %s -R %s' % (remote_env, remote_env_dir))
        run('supervisorctl start all')


def prepare_deploy():
    local_radon()
    local_flake8()
    local_update()
    local_test()


def deploy():
    if 'dev' in env.roles:
        remote_pull('dev')
    elif 'prod' in env.roles:
        remote_pull('prod')
    else:
        print(':)')
