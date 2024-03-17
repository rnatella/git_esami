#!/bin/bash

if [[ "$VIRTUAL_ENV" == "" ]]
then
    echo "Not running within virtualenv, quitting."
    exit 1
fi

PYTHON=${VIRTUAL_ENV}/bin/python3



if [ ! -e "./students.db" ]
then
    echo "Students DB not yet initialized, quitting."
    exit 1
fi

sqlite3 students.db 'SELECT DISTINCT user_subgroup FROM students ORDER BY user_subgroup ASC;'


