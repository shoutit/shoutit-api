FROM python:2.7

ARG SHOUTIT_ENV=dev

# Define working directory and copy files to it
RUN mkdir /api
WORKDIR /api
ADD . /api/

# Add external files
ADD https://s3-eu-west-1.amazonaws.com/shoutit-api-static/ip2location/IP2LOCATION-LITE-DB9.BIN /opt/ip2location/

# Install ubuntu dependencies
RUN apt-get update -y && apt-get install tesseract-ocr -y

# Install supervisor
RUN pip install supervisor
COPY ./deploy/supervisord.conf /etc/supervisord.conf

# Install pip requirements
RUN pip install -r src/requirements/${SHOUTIT_ENV}.txt
RUN pip install -r src/requirements/common_noupdate.txt

EXPOSE 8001

ENV PYTHONUNBUFFERED 1
ENV PYTHONIOENCODING UTF-8
ENV SHOUTIT_ENV $SHOUTIT_ENV
ENV NEW_RELIC_CONFIG_FILE /api/deploy/newrelic-${SHOUTIT_ENV}.ini

CMD gunicorn src.wsgi -c /api/src/settings_gunicorn.py
