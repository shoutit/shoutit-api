FROM python:3.6

ENV PYTHONUNBUFFERED 1

# Install Debian dependencies
RUN apt-get update && apt-get install -y \
    htop \
    tesseract-ocr \
    unzip \
    vim \
 && rm -rf /var/lib/apt/lists/*

# Add IP2Location Lite Database
RUN mkdir -p /opt/ip2location && \
    cd /opt/ip2location && \
    curl -sS -o /opt/ip2location/IP2LOCATION-LITE-DB9.BIN.ZIP \
    https://s3-eu-west-1.amazonaws.com/shoutit-api-static/ip2location/IP2LOCATION-LITE-DB9.BIN.ZIP?v=201708 && \
    unzip IP2LOCATION-LITE-DB9.BIN.ZIP && rm IP2LOCATION-LITE-DB9.BIN.ZIP

# Install pip requirements
COPY ./requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# Define working directory and copy files to it
RUN mkdir /api
WORKDIR /api
ADD . /api/

# Expose Gunicorn port
EXPOSE 8001

# Command to serve API
CMD ["newrelic-admin", "run-program", "gunicorn", "src.wsgi", "-c", "/api/deploy/gunicorn.py"]

# Command to run RQ
#CMD ["circusd", "/api/deploy/circus.ini"]
