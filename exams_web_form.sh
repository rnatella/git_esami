#!/bin/bash

export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000

if [ ! -e .flaskenv ]
then
	echo "SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)" > .flaskenv
fi

if [ "${SERVER_IP}" == "" ]
then

	echo "You should set the SERVER_IP environment var with the public IP address."
	read -p "Do you want to continue (y/n): " CONFIRM

	case "${CONFIRM}" in
                n|N )
			exit 1
	esac
fi

flask  --app web_form_app  run
