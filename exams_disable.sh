#!/bin/bash

if [[ "$VIRTUAL_ENV" == "" ]]
then
    echo "Not running within virtualenv, quitting."
    exit 1
fi

PYTHON=${VIRTUAL_ENV}/bin/python3


SUBGROUPS_STR=$1

SUBGROUPS=()


if [ "${SUBGROUPS_STR}" != "" ]
then
	for SUBGROUP in ${SUBGROUPS_STR//,/ }
	do
		SUBGROUPS+=("${SUBGROUP}")
	done

else

	SUBGROUPS=($(./exams_list.sh))
fi


for SUBGROUP in "${SUBGROUPS[@]}"
do
    echo "Enabling: $SUBGROUP"

    $PYTHON enable_users.py --disable --subgroup $SUBGROUP
done


