#!/bin/bash
CONTAINER=mtw_psql:01
echo "docker run -d -e POSTGRES_PASSWORD=${POSTGRES_ROOT_PASSWORD} ${CONTAINER}"
docker run -d -e POSTGRES_PASSWORD=${POSTGRES_ROOT_PASSWORD} ${CONTAINER}
