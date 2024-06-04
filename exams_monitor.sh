#!/bin/bash

if [[ "$VIRTUAL_ENV" == "" ]]
then
    echo "Not running within virtualenv, quitting." 1>&2
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


if [ "${GITEA_GATEWAY}" == "" ]
then
	GITEA_CONTAINER=$(docker ps -aqf "name=gitea-app")
	GITEA_GATEWAY=$(docker inspect  -f '{{range.NetworkSettings.Networks}}{{println .Gateway}}{{end}}' ${GITEA_CONTAINER} |head -1)
fi

echo "Monitoring: ${SUBGROUPS[@]}"

#$PYTHON monitor_repo.py  -s ${SUBGROUPS[@]} --webhook_as_git_server_url
$PYTHON monitor_repo.py  -s ${SUBGROUPS[@]} --webhook_server="${GITEA_GATEWAY}"

