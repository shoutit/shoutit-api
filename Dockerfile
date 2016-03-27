FROM python:2.7

ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
ADD src/requirements/* /code/

RUN pip install -r dev.txt
RUN pip install -r common_noupdate.txt

ADD . /code/
