#!/bin/bash

GITEA_ADMIN_USERNAME="root"


echo "Initializing access token..."

TOKEN=$(docker exec --user git gitea-app  gitea admin user generate-access-token --username ${GITEA_ADMIN_USERNAME} --token-name accesstoken --scopes all,sudo | perl -n -e '/([a-z0-9]{30,})/; print $1')

if [ "x$TOKEN" == "x" ]
then
	echo "Unable to create access token for Gitea."
    exit 1
else
	echo "Gitea access token: $TOKEN"
fi


GITEA_TOML="$( dirname -- "$BASH_SOURCE"; )/../gitea.toml"

echo "Updating token in Gitea client configuration (${GITEA_TOML})..."

perl -p -i -e 'if(/^token/) { s|'\''.*'\''|'\'"${TOKEN}"\''| }' $GITEA_TOML



