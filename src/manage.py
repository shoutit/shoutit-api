#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    # include the BACKEND_DIR in sys.path a.k.a PYTHONPATH to be able to use etc.env_settings for example.
    sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
