#!/bin/bash


if [[ "$VIRTUAL_ENV" == "" ]]
then
    echo "Not running within virtualenv, quitting."
    exit 1
fi

PYTHON=${VIRTUAL_ENV}/bin/python3



if [ "$#" -lt 3 ]
then
    echo "Usage: $0 <subgroup-name-prefix> <number-of-students-per-classroom> <path-to-code-folder> [classroom,classroom,...]"
    exit 1
fi

SUBGROUP_PREFIX=$1
STUDENTS=$2
REPO_REFERENCE=$3
SUBGROUPS_STR=$4


if [[ "${SUBGROUP_PREFIX}" == "" ]]
then
    echo "First parameter should be a string prefix (e.g., "esame-2023-07")"
    exit 1
fi


if [[ ! ${STUDENTS} =~ ^[0-9]+$ ]]
then
    echo "Second parameter should be an integer (the number of students to initialize, per classroom)"
    exit 1
fi

if [[ ! -d ${REPO_REFERENCE} ]]
then
    echo "Third parameter should be valid path of folder with code"
    exit 1
fi

SUBGROUPS=()

if [ "${SUBGROUPS_STR}" != "" ]
then
	for SUBGROUP in ${SUBGROUPS_STR//,/ }
	do
		SUBGROUPS+=("${SUBGROUP_PREFIX}-${SUBGROUP}")
	done

else
	SUBGROUPS=("${SUBGROUP_PREFIX}")
fi




for SUBGROUP in "${SUBGROUPS[@]}"
do

    echo
    echo "Initializing subgroup: $SUBGROUP"
    echo

    mkdir ./$SUBGROUP

    $PYTHON create_repo.py -n $STUDENTS -s $SUBGROUP --repo ./$SUBGROUP --ref $REPO_REFERENCE -b gitea

done


