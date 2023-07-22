#!/bin/bash

#if docker container inspect -f '{{.State.Running}}' gitea-app >/dev/null 2>&1
if docker volume ls | grep "gitea_gitea_app" >/dev/null
then

	echo "Gitea server was already configured. This script will stop, delete and re-configure it."
	read -p "If you want to continue, type 'y': " CONFIRM

	case "${CONFIRM}" in 
		y|Y )
			echo "Removing old configuration..."

			docker-compose down
			docker container prune --force
			docker volume prune --force

			echo "done.";;

		* )
			echo "Quitting"
			exit 0;;
	esac
fi


cp .env.dist .env

MYSQL_ROOT_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
MYSQL_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

echo "MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}" >> .env
echo "MYSQL_PASSWORD=${MYSQL_PASSWORD}" >> .env


GITEA_ADMIN_USERNAME="root"


echo "Enter Gitea admin password: "
read GITEA_ADMIN_PASSWORD

echo "Enter Gitea hostname (e.g., public IP): "
read GITEA_HOSTNAME


echo "GITEA_HOSTNAME=${GITEA_HOSTNAME}" >> .env


GITEA_BASE_URL="http://${GITEA_HOSTNAME}:3000"
echo "GITEA_BASE_URL=${GITEA_BASE_URL}" >> .env


GITEA_TOML="$( dirname -- "$BASH_SOURCE"; )/../gitea.toml"

echo "Updating Gitea client configuration (${GITEA_TOML})..."

perl -p -i -e 'if(/^url/)   { s|'\''.*'\''|'\'"${GITEA_BASE_URL}"\''| }' $GITEA_TOML



# from https://stackoverflow.com/questions/19331497/set-environment-variables-from-file-of-key-value-pairs
export $(grep -v '^#' .env | xargs)


docker-compose up -d


sleep 5

echo "Initial configuration of Gitea server, please wait..."

curl -s 'http://'"${GITEA_HOSTNAME}"':3000/' -X POST  -H 'Content-Type: application/x-www-form-urlencoded' --data-raw 'db_type=mysql&db_host=db%3A3306&db_user='"${MYSQL_USER}"'&db_passwd='"${MYSQL_PASSWORD}"'&db_name='"${MYSQL_DATABASE}"'&ssl_mode=disable&charset=utf8mb4&db_schema=&db_path=%2Fdata%2Fgitea%2Fgitea.db&app_name=Gitea%3A+Git+with+a+cup+of+tea&repo_root_path=%2Fdata%2Fgit%2Frepositories&lfs_root_path=%2Fdata%2Fgit%2Flfs&run_user=git&domain='"${GITEA_HOSTNAME}"'&ssh_port=22&http_port=3000&app_url=http%3A%2F%2F'"${GITEA_HOSTNAME}"'%3A3000%2F&log_root_path=%2Fdata%2Fgitea%2Flog&smtp_addr=&smtp_port=&smtp_from=&smtp_user=&smtp_passwd=&offline_mode=on&disable_gravatar=on&disable_registration=on&default_keep_email_private=on&no_reply_address=noreply.localhost&password_algorithm=pbkdf2&admin_name='"${GITEA_ADMIN_USERNAME}"'&admin_email=admin%40example.com&admin_passwd='"${GITEA_ADMIN_PASSWORD}"'&admin_confirm_passwd='"${GITEA_ADMIN_PASSWORD}"'' >/dev/null

sleep 30

