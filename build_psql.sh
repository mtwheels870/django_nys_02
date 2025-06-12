#!/bin/bash
BUILDKIT="DOCKER_BUILDKIT=1"
DOCKER_BUILD="docker build"
SECRET="--secret id=psql_password,env=POSTGRES_PASSWORD"
REST="-f Dockerfile.psql -t mtw_psql:01 ."
CMD="${BUILDKIT} ${DOCKER_BUILD} ${SECRET} ${REST}"
echo $CMD
eval $CMD
