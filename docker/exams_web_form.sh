#!/bin/bash

docker run --rm -it -v ./db:/app/db -v ./flask_session:/app/flask_session -e SERVER_IP=${SERVER_IP} --network host  git_esami  exams_web_form.sh
