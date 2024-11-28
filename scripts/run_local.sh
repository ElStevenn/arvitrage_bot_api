#!/bin/bash

container_port=8080
network_name="my_network"
image_name="funding_rate"
container_name="funding_ratev1"

if docker ps -a --format '{{.Names}}' | grep -q "^$container_name$"; then
    docker container stop "$container_name"
    docker container rm "$container_name"
fi

if docker images --format '{{.Repository}}' | grep -q "^$image_name$"; then
    docker image rm "$image_name"
fi

echo "Build and run container? (y/n)"
read response

if [ "$response" == "y" ]; then
    source scripts/run_local.sh
else
    echo "Operation aborted."
fi
