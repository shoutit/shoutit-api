Shoutit Backend
====================

Structure
====================

* Environment Dir: /opt/<env name>
* bin
* lib
* include
* backend
* assets
* docs
* etc
* env_settings.py
* gunicorn_settings.py
* src
* fabfile.py
* readme.md
* start.sh
* static
* media


Env Name: shoutit_backend_[dev|prod]

Log Dir: /var/opt/log/<env name>

Requirements
====================



Debian Requirements
--------------------
python-dev
libpq-dev
nginx
supervisor
python-pip
tcl8.5
libjpeg-dev
redis [https://www.digitalocean.com/community/tutorials/how-to-install-and-use-redis]


etc/hosts
--------------------
10.133.201.182  db.shoutit.com



General Python Requirements
--------------------
pip
virtualenvwrapper


.bachrc
--------------------
export WORKON_HOME=/opt
export PROJECT_HOME=/opt/dev
export VIRTUALENVWRAPPER_VIRTUALENV_ARGS='--no-site-packages'
source /usr/local/bin/virtualenvwrapper.sh

for fancy colors you can also add content of
etc/fancy_bashrc


id_rsa
--------------------
ssh-keygen


virtualenv
--------------------
/opt/shoutit_backend_[prod|dev]


backend dir
--------------------
git clone git@bitbucket.org:shoutitcom/shoutit_backend.git .


backend python requirements
--------------------
pip install -r 