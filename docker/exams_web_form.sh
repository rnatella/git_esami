#!/bin/bash

docker run --rm -it -v ./db:/app/db -v ./flask_session:/app/flask_session -p ${FLASK_RUN_PORT}:${FLASK_RUN_PORT} -e GIT_SERVER_IP=${GIT_SERVER_IP} -e FLASK_USE_HTTPS=${FLASK_USE_HTTPS} -e FLASK_RUN_PORT=${FLASK_RUN_PORT} -e FLASK_RUN_HOST=${FLASK_RUN_HOST}  git_esami  exams_web_form.sh
