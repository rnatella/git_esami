#!/bin/bash

export $(grep -v '^#' .env | xargs)

docker exec -it gitea-app bash -c "cd /data/gitea; gitea cert --host ${GITEA_HOSTNAME}; chown git:git cert.pem key.pem"

docker cp gitea-app:/data/gitea/conf/app.ini .

perl -p -i -e 's|http://|https://|' app.ini

cat << EOF >> app.ini

[server]
PROTOCOL            = https
CERT_FILE           = /data/gitea/cert.pem
KEY_FILE            = /data/gitea/key.pem
REDIRECT_OTHER_PORT = true
PORT_TO_REDIRECT    = 3080
EOF

docker cp app.ini gitea-app:/data/gitea/conf/

rm app.ini


GITEA_TOML="$( dirname -- "$BASH_SOURCE"; )/../gitea.toml"

echo "Updating Gitea client configuration (${GITEA_TOML})..."

perl -p -i -e 's|http://|https://|' $GITEA_TOML


echo "Updating container environment variables..."

perl -p -i -e 's|http://|https://|' .env


echo
echo "Restarting containers..."
echo

docker-compose down
docker-compose up -d

