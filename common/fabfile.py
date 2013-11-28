from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
import datetime, time, os

env.password = '$Yr3xrooT#'
env.hosts = ['root@50.56.191.101:7822']
env.warn_only = True

version_file_name = 'current_version.txt'

local_deployment = 'D:\\Syrex\\deployment\\'
local_code = 'D:\\Syrex\\local_deployment\\'

remote_home = '/home/django/'
remote_code = '/home/django/Shout/'
remote_deployment = '/home/django/deployment/'
remote_db_backup = '/home/django/db_backups/'

def update_local():
	with lcd(local_code):
		local('svn update')
		local('python manage.py makemessages -a -d djangojs')
		local('python manage.py makemessages -a')
		local('python manage.py compilemessages')
	with lcd(os.path.join(local_code, 'locale')):
		local('svn commit')

def test():
	with lcd(local_code):
		local('python manage.py test ShoutWebsite')

def backup_db(version='1.0'):
	result = sudo('cd %s && pg_dump shoutdb -T \'"ActivityLogger_*"\' | gzip -c > shoutdb.dump.before-%s.%s.out.gz' % (remote_db_backup, version.replace('.', '-'), time.strftime('%Y%m%d%H%M%S')), pty=False, user='postgres')
	if result.failed and not confirm("Could not backup database. Continue anyway?"):
		abort("Aborting at user request.")

def reflect_changes():
	with lcd(local_deployment):
		result = local('del settings.py')
		if result.failed and not confirm("Could not delete file. Continue anyway?"):
			abort("Aborting at user request.")

	def del_rec(dir):
		dir_path = os.path.join(local_deployment, dir)
		opposite_dir_path = os.path.join(local_code, dir)
		contents = os.listdir(dir_path)
		files = [f for f in contents if os.path.isfile(os.path.join(dir_path, f))]
		directories = [f for f in contents if os.path.isdir(os.path.join(dir_path, f)) and f != '.svn']

		for file in files:
			if not os.path.exists(os.path.join(opposite_dir_path, file)):
				with lcd(dir_path):
					result = local('svn delete --force ' + file)
					if result.failed and not confirm("Could not delete file. Continue anyway?"):
						abort("Aborting at user request.")

		for directory in directories:
			del_rec(os.path.join(dir, directory))
			if not os.path.exists(os.path.join(opposite_dir_path, directory)):
				with lcd(dir_path):
					result = local('svn delete --force ' + directory)
					if result.failed and not confirm("Could not delete directory. Continue anyway?"):
						abort("Aborting at user request.")

	del_rec('')

	include_file = open('include.txt')
	
	def mkdirs(path):
		if not os.path.exists(path):
			local('mkdir ' + path)
	
	for line in include_file:
		line = line.strip()
		if line.endswith('*'):
			line = line[:-1]
			dirs = line.split('/')
			dir = os.path.join(local_code, *dirs)
			contents = os.listdir(dir)
			files = [f for f in contents if os.path.isfile(os.path.join(dir, f))]
			mkdirs(os.path.join(local_deployment, *dirs))
			for f in files:
				local('copy /Y "' + os.path.join(dir, f) + '" "' + os.path.join(local_deployment, *(dirs + [f])) + '"')
		else:
			dirs, f = os.path.split(line)
			dirs = dirs.split('/')
			dir = os.path.join(local_code, *dirs)
			mkdirs(os.path.join(local_deployment, *dirs))
			local('copy /Y "' + os.path.join(dir, f) + '" "' + os.path.join(local_deployment, *(dirs + [f])) + '"')
			
	with lcd(local_deployment):
		local('ren deployment_settings.py settings.py')

def commit_local(version='1.0'):
	with lcd(local_deployment):
		local('svn add --force ./')
		local('svn commit -m "Deployment version: ' + version + '"')
	
def get_current_version(major='1'):
	try:
		version_file = open(version_file_name, 'r')
		p_major, p_minor = version_file.readlines()[-1][26:].strip().split('.')
		version_file.close()
	except IOError:
		p_major = ''
		p_minor = ''
	if int(p_major) > int(major):
		major = p_major
	if major == p_major:
		minor = str(int(p_minor) + 1)
	else:
		minor = '0'
	return '%s.%s' % (major, minor)

def prepare_deploy(with_test='', major='1'):
	if with_test:
		test()
	update_local()
	reflect_changes()
	current_version = get_current_version(major)
	commit_local(current_version)
	
	version_file = open(version_file_name, 'a')
	time_stamp = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S') + str.format('{0:+06.2f}', -float(time.timezone) / 3600).replace('.', ':')
	version_file.write('%s %s\n' % (time_stamp, current_version))
	version_file.close()
	return current_version

def deploy(with_test='', no_db='', major='1'):
	current_version = prepare_deploy(with_test, major)
	with cd(remote_deployment):
		run('svn update')
	result = run('service shout-celery stop')
	if result.failed and not confirm("Could not stop celery service. Continue anyway?"):
		abort("Aborting at user request.")
	result = run('service redis-server stop')
	if result.failed and not confirm("Could not stop redis service. Continue anyway?"):
		abort("Aborting at user request.")
	result = run('service shout stop')
	if result.failed and not confirm("Could not stop shout service. Continue anyway?"):
		abort("Aborting at user request.")
	result = run('service realtime stop')
	if not no_db:
		backup_db(current_version)
	if result.failed and not confirm("Could not stop realtime service. Continue anyway?"):
		abort("Aborting at user request.")
	with cd(remote_home):
		result = run('rm -R Shout')
		if result.failed and not confirm("Could not remove old Shout folder. Continue anyway?"):
			abort("Aborting at user request.")
	with cd(remote_deployment):
		run('svn export . ' + remote_code)
	with cd(remote_home):
		run('chown -R django Shout')
		run('chgrp -R django Shout')
		run('chmod -R 775 Shout')
	run('ln -s /usr/local/lib/python2.7/dist-packages/django/contrib/admin/media /home/django/Shout/ShoutWebsite/static/admin')
	run('service redis-server start')
	with cd(remote_code):
		run('python delete_cache.py')
	run('service shout start')
	run('service shout-celery start')
	run('service realtime start')