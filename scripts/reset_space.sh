#!/bin/bash

# Configuration
mongo_image="mongo"
mongodb_container="mongodb_v1"
network_name="my_network"

# Stop and remove the MongoDB container
if docker ps --format '{{.Names}}' | grep -q "^$mongodb_container$"; then
    echo "Stopping container '$mongodb_container'."
    docker stop "$mongodb_container"
else
    echo "Container '$mongodb_container' is not running."
fi

if docker ps -a --format '{{.Names}}' | grep -q "^$mongodb_container$"; then
    echo "Removing container '$mongodb_container'."
    docker rm "$mongodb_container"
else
    echo "Container '$mongodb_container' does not exist."
fi

# Check if the network exists
if docker network inspect "$network_name" &>/dev/null; then
    echo "Inspecting network '$network_name' for connected containers..."

    # Get a list of container names connected to the network
    container_names=$(docker network inspect -f '{{range $key, $value := .Containers}}{{$value.Name}} {{end}}' "$network_name")

    if [ -n "$container_names" ]; then
        echo "Found containers connected to the network: $container_names"

        # Loop through the containers and disconnect them
        for container in $container_names; do
            echo "Disconnecting container '$container' from network '$network_name'."
            docker network disconnect "$network_name" "$container"
        done
    else
        echo "No containers connected to the network."
    fi

    # Remove the network
    echo "Removing network '$network_name'."
    docker network rm "$network_name"

    echo "Network '$network_name' removed successfully."
else
    echo "Network '$network_name' does not exist."
fi
