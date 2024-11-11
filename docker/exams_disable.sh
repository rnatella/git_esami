#!/bin/bash

docker run --rm -it -v ./db:/app/db --network host  git_esami  exams_disable.sh "$@"
