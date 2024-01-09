#!/bin/bash

export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000
echo "SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)" > .flaskenv
flask  --app web_form_app run
