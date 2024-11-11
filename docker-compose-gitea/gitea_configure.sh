#!/bin/bash

#if docker container inspect -f '{{.State.Running}}' gitea-app >/dev/null 2>&1
if docker volume ls | grep "gitea_gitea_app" >/dev/null
then

	echo "Gitea server was already configured. This script will stop, delete and re-configure it."
	read -p "If you want to continue, type 'y': " CONFIRM

	case "${CONFIRM}" in 
		y|Y )
			echo "Removing old configuration..."

			#docker compose down
			docker compose down -v
			docker container prune --force
			docker volume prune --force
			docker network prune --force

			echo "done.";;

		* )
			echo "Quitting"
			exit 0;;
	esac
fi


cp .env.dist .env

MYSQL_ROOT_PASSWORD=$(LC_ALL=C bash -c 'cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1')
MYSQL_PASSWORD=$(LC_ALL=C bash -c 'cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1')

echo "MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}" >> .env
echo "MYSQL_PASSWORD=${MYSQL_PASSWORD}" >> .env
echo "GITEA_SSH_PORT=22222" >> .env


GITEA_ADMIN_USERNAME="root"


read -p "Enter Gitea admin password: " -s GITEA_ADMIN_PASSWORD
echo

if [ "${GITEA_ADMIN_PASSWORD}" == "" ]
then
	echo "You need to enter a password."
	exit 1
fi



read -p "Enter Gitea hostname (default=0.0.0.0): " GITEA_HOSTNAME
GITEA_HOSTNAME=${GITEA_HOSTNAME:-"0.0.0.0"}

read -p "Enter Gitea port (default=3000): " GITEA_PORT
GITEA_PORT=${GITEA_PORT:-3000}


GITEA_PROTOCOL="http"



echo "GITEA_HOSTNAME=${GITEA_HOSTNAME}" >> .env


GITEA_BASE_URL="${GITEA_PROTOCOL}://${GITEA_HOSTNAME}:${GITEA_PORT}"
echo "GITEA_BASE_URL=${GITEA_BASE_URL}" >> .env


GITEA_TOML="$( dirname -- "$BASH_SOURCE"; )/../gitea.toml"

if [ ! -e $"{GITEA_TOML}" ]
then

cat << EOF > ${GITEA_TOML}
[global]
default = "local"

[local]
url = '${GITEA_BASE_URL}'
token = '<TOKEN>'
EOF

fi


echo "Updating Gitea client configuration (${GITEA_TOML})..."

perl -p -i -e 'if(/^url/)   { s|'\''.*'\''|'\'"${GITEA_BASE_URL}"\''| }' $GITEA_TOML



# from https://stackoverflow.com/questions/19331497/set-environment-variables-from-file-of-key-value-pairs
export $(grep -v '^#' .env | xargs)


docker compose build
docker compose up -d


sleep 10

CURL_OPTIONS=""

if [ ${GITEA_PROTOCOL} == "https" ]
then
	CURL_OPTIONS="--insecure"
fi

echo "Initial configuration of Gitea server, please wait..."

curl ${CURL_OPTIONS} -s ${GITEA_BASE_URL} -X POST  -H 'Content-Type: application/x-www-form-urlencoded' --data-raw 'db_type=mysql&db_host=db%3A3306&db_user='"${MYSQL_USER}"'&db_passwd='"${MYSQL_PASSWORD}"'&db_name='"${MYSQL_DATABASE}"'&ssl_mode=disable&charset=utf8mb4&db_schema=&db_path=%2Fdata%2Fgitea%2Fgitea.db&app_name=Gitea%3A+Git+with+a+cup+of+tea&repo_root_path=%2Fdata%2Fgit%2Frepositories&lfs_root_path=%2Fdata%2Fgit%2Flfs&run_user=git&domain='"${GITEA_HOSTNAME}"'&ssh_port=22&http_port='"${GITEA_PORT}"'&app_url='"${GITEA_PROTOCOL}"'%3A%2F%2F'"${GITEA_HOSTNAME}"'%3A'"${GITEA_PORT}"'%2F&log_root_path=%2Fdata%2Fgitea%2Flog&smtp_addr=&smtp_port=&smtp_from=&smtp_user=&smtp_passwd=&offline_mode=on&disable_gravatar=on&disable_registration=on&default_keep_email_private=on&no_reply_address=noreply.localhost&password_algorithm=pbkdf2&admin_name='"${GITEA_ADMIN_USERNAME}"'&admin_email=admin%40example.com&admin_passwd='"${GITEA_ADMIN_PASSWORD}"'&admin_confirm_passwd='"${GITEA_ADMIN_PASSWORD}"'' -o /dev/null -s -w "%{http_code}\n"

if [ $? -ne 0 ]
then
	echo "Error: HTTP failure with CURL at ${GITEA_BASE_URL}"
	exit 1
fi

sleep 30

