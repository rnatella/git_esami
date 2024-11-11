#!/bin/bash

docker run --rm -it -v ./db:/app/db -v ./repos:/app/repos --network host  git_esami  exams_pull_repos.sh "$@"
