#!/bin/bash

# Configuration
mongodb_container="mongodb_v1"
network="my_network"
volume="data_volume"



# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed" > error.txt
    exit 125
else
    echo "Docker is installed"
fi

# Ensuring container
if ! docker volume ls --format '{{.Name}}' | grep -q "^$volume"; then
    echo "Creating volume"
    docker volume create $volume
fi

# Ensure MongoDB container is running
if docker ps -a --format '{{.Names}} {{.State}}' | grep -q "^$mongodb_container "; then
    if docker ps --format '{{.Names}}' | grep -q "^$mongodb_container$"; then
        echo "Container '$mongodb_container' is running."
    else
        echo "Starting container '$mongodb_container'."
        docker start $mongodb_container
    fi
else
    echo "Creating MongoDB container '$mongodb_container'."
    docker pull mongo
        docker run -d \
        --name $mongodb_container \
        --network $network \
        --volume $volume_name:/data/db \
        -e MONGO_INITDB_ROOT_USERNAME=root \
        -e MONGO_INITDB_ROOT_PASSWORD=example \
        mongo
fi


# Ensure Docker network exists
if ! docker network ls --format '{{.Name}}' | grep -q "^$network$"; then
    echo "Creating Docker network '$network'."
    docker network create --driver bridge $network
fi

# Ensure MongoDB container is on the correct network
if ! docker inspect $mongodb_container | grep -q "\"Network\": \"$network\""; then
    echo "Connecting container '$mongodb_container' to network '$network'."
    docker network connect $network $mongodb_container
fi

# Jenkins setup

jenkins_container="jenkins-server"
jenkins_port=8080
jenkins_home="jenkins_home"

# Ensure Jenkins container is running
if docker ps -a --format '{{.Names}} {{.State}}' | grep -q "^$jenkins_container "; then
    if docker ps --format '{{.Names}}' | grep -q "^$jenkins_container$"; then
        echo "Jenkins container '$jenkins_container' is running."
    else
        echo "Starting Jenkins container '$jenkins_container'."
        docker start $jenkins_container
    fi
else
    echo "Creating Jenkins container '$jenkins_container'."
    docker run -d \
        --name $jenkins_container \
        -p $jenkins_port:8080 \
        -v $jenkins_home:/var/jenkins_home \
        -v /var/run/docker.sock:/var/run/docker.sock \
        jenkins/jenkins:lts
fi

# Wait for Jenkins to start
echo "Waiting for Jenkins to initialize (60 seconds)..."
sleep 60

# Trigger Jenkins pipeline via REST API
jenkins_url="http://localhost:$jenkins_port"
job_name="MyPipeline"
api_token="<your-api-token>"
username="<your-username>"

echo "Triggering Jenkins pipeline..."
curl -X POST "$jenkins_url/job/$job_name/build" \
     --user "$username:$api_token"

echo "Setup complete."
