###Debian Requirements
* tcl8.5
* libjpeg-dev #SBE-82 test

###virtualenv
* env_name: shoutit_api_[dev|prod|local]
* env_dir: /opt/{env_name}
* log_dir: {env_dir}/log
* api_dir: {env_dir}/api

###api_dir
* git clone git@bitbucket.org:shoutitcom/shoutit_api.git .
