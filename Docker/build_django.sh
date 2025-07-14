#!/bin/bash
BUILDKIT="DOCKER_BUILDKIT=1"
DOCKER_BUILD="docker build"
CACHE="--no-cache"
PASSWORD01="--build-arg PASSWORD01='stuff_here'"
REST="-f Dockerfile.django -t mtw:01 .."
VOLUME=""
CMD="${BUILDKIT} ${DOCKER_BUILD} ${CACHE} ${PASSWORD_ROOT} ${PASSWORD_USER} ${VOLUME} ${REST}"
echo $CMD
eval $CMD
