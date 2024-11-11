#!/bin/bash

export FLASK_RUN_HOST=${FLASK_RUN_HOST:-0.0.0.0}
export FLASK_RUN_PORT=${FLASK_RUN_PORT:-8000}

if [ ! -e .flaskenv ]
then
	echo "SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)" > .flaskenv
fi

if [ "${GIT_SERVER_IP}" == "" ]
then

	echo "You should set the GIT_SERVER_IP environment var with an IP address."
	echo "This IP address will be shown to clients as the IP of the Git server."
	read -p "Do you want to continue? (y/n): " CONFIRM

	case "${CONFIRM}" in
                n|N )
			exit 1
	esac
fi

CERT_FLAGS=""

if [ "${FLASK_USE_HTTPS}" != "" ]
then
	CERT_FLAGS="--cert=adhoc"
fi

flask  --app web_form_app  run  $CERT_FLAGS
