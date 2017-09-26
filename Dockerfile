FROM python:3.6

ENV PYTHONUNBUFFERED 1

# Install Debian dependencies
RUN apt-get update && apt-get install -y \
    htop \
    tesseract-ocr \
    unzip \
    vim \
 && rm -rf /var/lib/apt/lists/*

# Install dockerize
ENV DOCKERIZE_VERSION v0.5.0
RUN wget -nv https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

# Define working directory
RUN mkdir /api
WORKDIR /api

# Add IP2Location Lite Database
RUN mkdir -p meta/ip2location \
 && cd meta/ip2location \
 && curl -sS -o IP2LOCATION-LITE-DB9.BIN.ZIP https://s3-eu-west-1.amazonaws.com/shoutit-api-static/ip2location/IP2LOCATION-LITE-DB9.BIN.ZIP?v=201708 \
 && unzip IP2LOCATION-LITE-DB9.BIN.ZIP && rm IP2LOCATION-LITE-DB9.BIN.ZIP

# Install Python requirements
COPY ./requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# Copy project files to working directory
COPY . .

# Expose Gunicorn port
EXPOSE 8001

# Command to serve API
CMD ["newrelic-admin", "run-program", "gunicorn", "src.wsgi", "-c", "deploy/gunicorn.py"]

# Command to run RQ
#CMD ["circusd", "deploy/circus.ini"]
