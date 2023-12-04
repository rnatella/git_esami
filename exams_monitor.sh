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

SUBGROUPS=()

DOCENTI=
DOCENTI_CFG=".docenti.txt"

if [ -e ${DOCENTI_CFG} ]
then
	DOCENTI=($(cat ${DOCENTI_CFG} | tr ',' '\n'))
else
	echo "Error: list of classrooms not found"
	exit 1
fi



for DOCENTE in "${DOCENTI[@]}"
do
    SUBGROUPS+=("$SUBGROUP_PREFIX-$DOCENTE")
done


echo "Monitoring: ${SUBGROUPS[@]}"

$PYTHON monitor_repo.py  -s ${SUBGROUPS[@]} --webhook_as_git_server_url

