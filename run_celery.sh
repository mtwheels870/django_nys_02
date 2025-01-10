#!/bin/bash

LOG_DIR=/tmp/pp_celery
if [ ! -d $LOG_DIR ]; then
    echo mkdir $LOG_DIR
    mkdir $LOG_DIR
fi

LOG_FILE=celery_"$(date +'%FT%H%m').txt"
FULL_FILE=$LOG_DIR/$LOG_FILE

RUN_DIR=./django_nys_02
LOG_LEVEL=INFO
APP_NAME=tasks

echo cd $RUN_DIR
cd $RUN_DIR
celery -A $APP_NAME worker --loglevel=$LOG_LEVEL | tee $FULL_FILE
