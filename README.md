### Env variables

`SHOUTIT_ENV` should be set before starting the server. These (except `SHOUTIT_ENV`) should be set in an `.env` file located in `src/configs`.
The filename should match `SHOUTIT_ENV` value e.g if it is `local` the file should be `local.env`.

| Name                                          | Default       | Notes                                                          |
|-----------------------------------------------|---------------|----------------------------------------------------------------|
| `API_LINK`                                    |               |                                                                |
| `DB_HOST`,`DB_PORT`, `DB_USER`, `DB_PASSWORD` |               |                                                                |
| `EMAIL_ENV`                                   |               | Can be either `file` or `sendgrid`                             |
| `ES_HOST`, `ES_PORT`, `ES_BASE_INDEX`         |               |                                                                |
| `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`      |               |                                                                |
| `FORCE_SYNC_RQ`                               | `False`       | When true, RQ jobs will be executed on the same request thread |
| `MIXPANEL_TOKEN`                              |               |                                                                |
| `PUSHER_ENV`                                  | `SHOUTIT_ENV` value |                                                                |
| `RAVEN_DSN`                                   |               | whennot provided Sentry won't be used for logging errors       |
| `REDIS_HOST`,`REDIS_PORT`                     |               |                                                                |
| `SHOUTIT_DEBUG`                               |               | Any truth value                                                |
| `SHOUTIT_ENV`                                 |               | Should be one of the following: `prod`, `dev` or `local`       |
| `SITE_LINK`                                   |               |                                                                |
| `TWILIO_ENV`                                  | `SHOUTIT_ENV` value|                                                                |


Other loadbalancer related variables that can be used on Docker. They should be also set outside the .

- `FORCE_SSL`
- `VIRTUAL_HOST`

Tests
-----

#### Run locally

    pip install -r requirements/test.txt
    cd shoutit-api/src

    # use fabric
    fab local_test

    # OR manually run
    python manage.py test --keepdb

    # OR manually run with coverage
    coverage run --source='.' manage.py test --keepdb
    # report only v3
    coverage report --omit='tests/*,*migrations*,*management*,*/v2/*,wsgi.py,manage.py,settings*'

#### Run inside docker

Make sure, that all services are able to listen requests from docker (i.e. not only localhost). The easiest way is to let them listen on 0.0.0.0.

At least following services are required to run on your host:

- postgres
- elasticsearch
- redis

Then run docker:

    docker build --build-arg SHOUTIT_ENV=test -t shoutit/shoutit-api:test .
    docker run -it --add-host host_machine:$(ip addr show docker0 | grep "inet\b" | awk '{print $2}' | cut -d/ -f1) shoutit/shoutit-api:test coverage run --source='.' src/manage.py test --keepdb

Note, if you are using MacOS, the docker is run inside virtualbox. In that case replace 'docker0' with your virtualbox network interface name (for example vboxnet0). Use ifconfig command to find interface name.
