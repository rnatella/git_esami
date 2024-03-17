#!/bin/bash

echo "This script will delete everything from previous exams (DB, flask sessions, code repos)."
read -p "If you want to continue, type 'y': " CONFIRM

if [[ $CONFIRM != "y" ]]
then
    echo "Quitting"
    exit 1
fi

rm -f students.db
rm -rf flask_session
rm -f .flaskenv

docker stop gitea-app
docker rm gitea-app
docker volume rm  docker-compose-gitea_gitea_app

docker stop gitea-db
docker rm gitea-db
docker volume rm  docker-compose-gitea_gitea_db

