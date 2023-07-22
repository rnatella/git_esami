#!/bin/bash

if [[ "$VIRTUAL_ENV" == "" ]]
then
    echo "Not running within virtualenv, quitting."
    exit 1
fi

PYTHON=${VIRTUAL_ENV}/bin/python3



SUBGROUP_PREFIX=

if [[ -e .current_exam.txt ]]
then
    SUBGROUP_PREFIX=$(cat .current_exam.txt)
else
    echo "Enter subgroup prefix string (es. esame-2023-07): "
    read SUBGROUP_PREFIX
fi


for DOCENTE in cinque cotroneo natella
do
    SUBGROUP="${SUBGROUP_PREFIX}-${DOCENTE}"

    echo "Pulling repos: $SUBGROUP"

    $PYTHON check_repo.py -s $SUBGROUP  --pull --rename -r ./$SUBGROUP
done


