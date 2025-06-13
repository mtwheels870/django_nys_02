#!/bin/bash
BUILDKIT="DOCKER_BUILDKIT=1"
DOCKER_BUILD="docker build"
ROOT_PASSWORD="psql_root_password"
SECRET_ROOT="--secret id=${ROOT_PASSWORD},env=POSTGRES_PASSWORD"
USER_PASSWORD="psql_user_password"
SECRET_USER="--secret id=${USER_PASSWORD},env=POSTGRES_USER_PASSWORD"
REST="-f Dockerfile.psql -t mtw_psql:01 ."
CMD="${BUILDKIT} ${DOCKER_BUILD} ${SECRET_ROOT} ${SECRET_USER} ${REST}"
echo $CMD
eval $CMD
