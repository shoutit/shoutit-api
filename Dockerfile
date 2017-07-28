FROM python:3.6

# Install pip requirements
COPY ./requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# Install ubuntu dependencies
RUN apt-get update -y && apt-get install tesseract-ocr -y

# Add external files. curl is used instead of ADD to utilze cache
RUN mkdir /opt/ip2location && \
    curl -o /opt/ip2location/IP2LOCATION-LITE-DB9.BIN \
    https://s3-eu-west-1.amazonaws.com/shoutit-api-static/ip2location/IP2LOCATION-LITE-DB9.BIN?v=1

# Define working directory and copy files to it
RUN mkdir /api
WORKDIR /api
ADD . /api/

# Expose Gunicorn port
EXPOSE 8001

ENV PYTHONUNBUFFERED 1

# Command to serve API
CMD ["newrelic-admin", "run-program", "gunicorn", "src.wsgi", "-c", "/api/deploy/gunicorn.py"]

# Command to run RQ
#CMD ["circusd", "/api/deploy/circus.ini"]
