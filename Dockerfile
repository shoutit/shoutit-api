FROM python:3.5

# Install pip requirements
COPY ./requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# Install ubuntu dependencies
RUN apt-get update -y && apt-get install tesseract-ocr -y

# Install Gunicorn for serving Quant API endpoints
RUN pip install gunicorn==19.6.0

# Install circus
RUN pip install circus==0.14.0

# Add external files
ADD https://s3-eu-west-1.amazonaws.com/shoutit-api-static/ip2location/IP2LOCATION-LITE-DB9.BIN /opt/ip2location/

# Define working directory and copy files to it
RUN mkdir /api
WORKDIR /api
ADD . /api/

EXPOSE 8001

ENV PYTHONUNBUFFERED 1

# Command to serve API
CMD ["newrelic-admin", "run-program", "gunicorn", "src.wsgi", "-c", "/api/deploy/settings_gunicorn.py"]

# Command to run RQ workers
#CMD ["circusd", "/api/deploy/circus.ini"]
