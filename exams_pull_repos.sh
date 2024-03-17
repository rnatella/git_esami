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

    echo "Pulling repos: $SUBGROUP"

    $PYTHON check_repo.py -s $SUBGROUP  --pull --rename -r ./$SUBGROUP
done


