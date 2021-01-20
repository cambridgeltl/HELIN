#!/bin/bash

source variables.sh

docker image build --build-arg UID=$(id -u) --build-arg GID=$(id -g) --build-arg UNAME=$DOCKER_USER -t $IMAGE_NAME .
