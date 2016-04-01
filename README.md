###Debian Requirements
* tcl8.5
* libjpeg-dev #SBE-82 test

###virtualenv
* env_name: shoutit_api_[dev|prod|local]
* log_dir: /var/log/{env_name}
* api_dir: /opt/api

###api_dir
* git clone git@bitbucket.org:shoutitcom/shoutit_api.git .


### Env variables

- `ENV` should be one of these:
    - `shoutit_api_local`
    - `shoutit_api_dev`
    - `shoutit_api_prod`
- `DB_HOST`, `DB_PORT`
- `ES_HOST`, `ES_PORT`
- `REDIS_HOST`, `REDIS_PORT`
