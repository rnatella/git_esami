#!/bin/bash

export GITEA_CONTAINER=$(docker ps -aqf "name=gitea-app")
export GITEA_GATEWAY=$(docker inspect  -f '{{range.NetworkSettings.Networks}}{{println .Gateway}}{{end}}' ${GITEA_CONTAINER} |head -1)

docker run --rm -it -v ./db:/app/db -e GITEA_GATEWAY=${GITEA_GATEWAY} --network host  git_esami  exams_monitor.sh "$@"
