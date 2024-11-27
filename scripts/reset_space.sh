#!/bin/bash

# Configuration
mongodb_container="mongodb_v1"
network_name="my_network"
volume_name="data_volume"
key_path="src/security/secure_key"

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

# Remove the Docker volume
if docker volume ls --format '{{.Name}}' | grep -q "^$volume_name$"; then
    echo "Removing volume '$volume_name'."
    docker volume rm "$volume_name"
else
    echo "Volume '$volume_name' does not exist."
fi

# Remove the Docker network
if docker network ls --format '{{.Name}}' | grep -q "^$network_name$"; then
    echo "Removing network '$network_name'."
    docker network rm "$network_name"
else
    echo "Network '$network_name' does not exist."
fi

# Kill any process listening on port 27017
pid=$(sudo lsof -t -i:27017)
if [ "$pid" ]; then
    echo "Killing process on port 27017 with PID $pid."
    sudo kill -9 $pid
else
    echo "No process is listening on port 27017."
fi

# Remove the .env file and security keys
if [ -f "src/.env" ]; then
    echo "Removing src/.env file."
    rm src/.env
else
    echo "src/.env file does not exist."
fi

if [ -f "$key_path" ] || [ -f "$key_path.pub" ]; then
    echo "Removing security keys."
    rm -f "$key_path" "$key_path.pub"
else
    echo "Security keys do not exist."
fi

echo "Cleanup completed."
