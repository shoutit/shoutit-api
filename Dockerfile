FROM python:2.7

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
ADD src/requirements/* /code/

RUN pip install -r dev.txt
RUN pip install -r common_noupdate.txt

ADD . /code/
RUN wget -P /opt/ip2location https://s3-eu-west-1.amazonaws.com/shoutit-api-static/ip2location/IP2LOCATION-LITE-DB9.BIN
