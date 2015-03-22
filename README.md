#Shoutit API

##Structure

Environment Dir: /opt/{env name}

* bin
* lib
* include
* api
    * assets
    * docs
    * etc
        * env_settings.py
        * gunicorn_settings.py
    * src
    * fabfile.py
    * readme.md
* static
* media


##Requirements


###Debian Requirements
* python-dev
* libpq-dev
* nginx
* supervisor
* python-pip
* tcl8.5
* libjpeg-dev
* redis [https://www.digitalocean.com/community/tutorials/how-to-install-and-use-redis]


###etc/hosts
* 10.133.201.182  db.shoutit.com


###General Python Requirements
* pip
* virtualenvwrapper


###.bachrc
* export WORKON_HOME=/opt
* export PROJECT_HOME=/opt/dev
* export VIRTUALENVWRAPPER_VIRTUALENV_ARGS='--no-site-packages'
* source /usr/local/bin/virtualenvwrapper.sh

* for fancy colors you can also add content of `etc/fancy_bashrc`


###id_rsa
* ssh-keygen


###virtualenv
* env_name: shoutit_api_[dev|prod|local]
* env_dir: /opt/{env_name}
* log_dir: {env_dir}/log
* api_dir: {env_dir}/api


###api_dir
* git clone git@bitbucket.org:shoutitcom/shoutit_api.git .


###python requirements
* pip install -r 