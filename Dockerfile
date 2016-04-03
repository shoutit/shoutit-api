FROM python:2.7

ARG SHOUTIT_ENV=dev

# Define working directory and copying files to it
RUN mkdir /api
WORKDIR /api
ADD . /api/

# Install pip requirements
RUN pip install -r src/requirements/$SHOUTIT_ENV.txt
RUN pip install -r src/requirements/common_noupdate.txt

# Add external dependencies
ADD https://s3-eu-west-1.amazonaws.com/shoutit-api-static/ip2location/IP2LOCATION-LITE-DB9.BIN /opt/ip2location/

EXPOSE 8001

ENV PYTHONUNBUFFERED 1
ENV SHOUTIT_ENV $SHOUTIT_ENV

CMD gunicorn src.wsgi -c ./src/settings_gunicorn.py
