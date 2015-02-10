#!/bin/bash

DJANGO_SETTINGS_MODULE="settings"
DJANGO_WSGI_MODULE="wsgi"

BACKEND_DIR="${PWD}"
DJANGO_DIR="${BACKEND_DIR}/src"
ENV_DIR="$(dirname "${BACKEND_DIR}")"
ENV="$(basename "${ENV_DIR}")"
LOG_DIR="/var/log/opt/${ENV}"

source "${ENV_DIR}/bin/activate"

export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}
export PYTHONPATH=${BACKEND_DIR}:${DJANGO_DIR}:${PYTHONPATH}

export BACKEND_DIR=$BACKEND_DIR
export DJANGO_DIR=$DJANGO_DIR
export ENV_DIR=$ENV_DIR
export ENV=$ENV
export LOG_DIR=$LOG_DIR


echo "Starting ${ENV} as `whoami`"

cd ${DJANGO_DIR}
exec gunicorn ${DJANGO_WSGI_MODULE} --config ${BACKEND_DIR}/etc/gunicorn_settings.py
