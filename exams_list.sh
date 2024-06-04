#!/bin/bash

if [[ "$VIRTUAL_ENV" == "" ]]
then
    echo "Not running within virtualenv, quitting." 1>&2
    exit 1
fi

PYTHON=${VIRTUAL_ENV}/bin/python3


STUDENT_DB=${STUDENT_DB:="./db/students.db"}

if [ ! -e "${STUDENT_DB}" ]
then
    echo "Students DB not yet initialized, quitting." 1>&2
    exit 1
fi

sqlite3 ${STUDENT_DB} 'SELECT DISTINCT user_subgroup FROM students ORDER BY user_subgroup ASC;'


