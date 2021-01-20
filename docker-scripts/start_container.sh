#!/bin/bash

# Get the container name
source variables.sh

# Get the command-line parameters
ARG_MODE=${1:--i}
ARG_PORT=${2:-5000}

# Create a tmp folder in /tmp
mkdir -p /tmp/$IMAGE_NAME

# Parameter for docker run
WORKDIR="/home/$DOCKER_USER"
VOLUMES="-v $(pwd)/../src:${WORKDIR}/src"
NAME="--name ${CONTAINER_NAME} ${IMAGE_NAME}"
USER="--user $(id -u):$(id -g)"
PORT="-p ${ARG_PORT}:5000"

# Check the the port is valid
if [ $# -eq 2 ]; then
	if ! [[ ${ARG_PORT} =~ ^[0-9]+$ ]] ; then
		echo "The provided port must be a positive integer."
		exit 1 
    fi
fi

# Run the container in detached mode
if [ $# -eq 1 ] || [ $# -eq 2 ]; then
    if [ "$ARG_MODE" == "-d" ]; then
        ${DOCKER_BIN} run -d ${PORT} ${USER} ${VOLUMES} ${NAME} bash -c "cd src && python3 app.py"
        exit 0
    fi
fi

# Run the container in notebook mode
if [ $# -eq 1 ] || [ $# -eq 2 ]; then
    if [ "$ARG_MODE" == "-s" ]; then
        ${DOCKER_BIN} run --rm ${PORT} ${USER} ${VOLUMES} ${NAME} bash -c "cd src && python3 app.py"
        exit 0
    fi
fi

# Run the container in interactive mode
if [ $# -eq 0 ] || [ $# -eq 1 ] || [ $# -eq 2 ]; then
    if [ "$ARG_MODE" == "-i" ]; then
		${DOCKER_BIN} run -it --rm ${PORT} ${USER} ${VOLUMES} ${NAME}
		exit 0
    fi
fi

echo "start_container.sh MODE PORT: starts the container in interactive mode"
echo
echo "Modes:"
echo "  -i: (default) Starts the container in interactive mode"
echo "  -s: Starts the container and the Flask server"
echo "  -d: Starts the container (and the Flask server) in detached mode"
echo ""
echo "Port: binds the port used by the notebook server to the specified port in the host (default:5000)"
echo ""
echo "Example:"
echo "start_container.sh -n 8880 : Starts the container and the notebook server, binding the server to the port 8880"
echo ""
exit 1


