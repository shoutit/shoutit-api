import os
import sys

from celery.task import task

from django.conf import settings


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.dirname(__file__))

from django.core.management import setup_environ

setup_environ(settings)

@task(name='execute')
def execute(path, module_name, class_name, method_name, *args, **kwargs):
	try:
		if path:
			sys.path.insert(0, os.path.abspath(path))
		m = __import__(module_name, fromlist = class_name and [class_name] or [])
		if m.__name__ != module_name:
			modules = module_name.split('.')[1:]
			for module in modules:
				m = getattr(m, module)
		if class_name:
			c = getattr(m, class_name)
			f = getattr(c, method_name)
		else:
			f = getattr(m, method_name)
		if hasattr(f, 'func'):
			f = f.func
		return f(*args, **kwargs)
	except Exception, e:
		import traceback
		traceback.print_exc()
		raise e

