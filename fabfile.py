from __future__ import unicode_literals, with_statement

import os

from fabric.api import *

API_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.join(API_DIR, 'src')

manage_py = os.path.join(SRC_DIR, 'manage.py')
# Todo (mo): This works only on Windows (specifically my machine)
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
        local('pip list --outdated')


def local_test():
    with lcd(scripts_dir):
        with settings(warn_only=True):
            local('py.test %s --reuse-db --cov=src' % API_DIR)


def prepare_deploy():
    local_radon()
    local_flake8()
    local_update()
    local_test()
