#!/bin/bash

GROUP=$1
NUM_USERS=$2
REFERENCE_REPO=$3

docker run --rm -it -v ./db:/app/db -v ${REFERENCE_REPO}:/reference-repo -v ./repos:/app/repos --network host  git_esami  exams_create.sh  $GROUP  ${NUM_USERS}  /reference-repo
