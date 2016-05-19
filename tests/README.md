Tests
=====

#### Run locally

    pip install -r requirements/test.txt

    # use fabric
    fab local_test

    # OR manually run
    PYTHONPATH='./src' py.test --reuse-db --cov=src

#### Run inside docker

Make sure, that all services are able to listen requests from docker (i.e. not only localhost). The easiest way is to let them listen on 0.0.0.0.

At least following services are required to run on your host:

- postgres
- elasticsearch
- redis

Then run docker:

    docker build --build-arg SHOUTIT_ENV=test -t shoutit/shoutit-api:test .
    docker run -it --add-host host_machine:$(ip addr show docker0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1) shoutit/shoutit-api:test PYTHONPATH='./src' py.test --reuse-db --cov=src

Note, if you are using MacOS, the docker is run inside virtualbox. In that case replace 'docker0' with your virtualbox network interface name (for example vboxnet0). Use ifconfig command to find interface name.