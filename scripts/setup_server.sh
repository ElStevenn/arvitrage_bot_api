#!/bin/bash

# Configuration
mongodb_container="mongodb_v1"
network="my_network"
volume="data_volume"
key_path="src/security/secure_key"


install_docker() {
    # Function to install docker

    echo "Docker is not installed. Installing Docker and dependencies..."
    sudo apt-get update -yes
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

    sudo usermod -aG docker "$USER"
    echo "Docker installation complete. Please log out and back in to use Docker without sudo."
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    install_docker
else
    echo "Docker is installed"
fi

# Ensure Docker network exists
if ! docker network ls --format '{{.Name}}' | grep -q "^$network$"; then
    echo "Creating Docker network '$network'."
    docker network create --driver bridge $network
else
    echo "Docker network '$network' already exists."
fi

# Ensure volume exists
if ! docker volume ls --format '{{.Name}}' | grep -q "^$volume$"; then
    echo "Creating volume '$volume'."
    docker volume create $volume
else
    echo "Docker volume '$volume' already exists."
fi

# Ensure MongoDB container is running
if docker ps -a --format '{{.Names}}' | grep -q "^$mongodb_container$"; then
    if docker ps --format '{{.Names}}' | grep -q "^$mongodb_container$"; then
        echo "MongoDB container '$mongodb_container' is running."
    else
        echo "Starting MongoDB container '$mongodb_container'."
        docker start $mongodb_container
    fi
else
    echo "Creating MongoDB container '$mongodb_container'."
    docker pull mongo
    docker run -d \
        --name $mongodb_container \
        --network $network \
        --volume $volume:/data/db \
        -e MONGO_INITDB_ROOT_USERNAME=root \
        -e MONGO_INITDB_ROOT_PASSWORD=example \
        mongo
fi

# Ensure MongoDB container is on the correct network
if ! docker network inspect $network | grep -q "$mongodb_container"; then
    echo "Connecting MongoDB container '$mongodb_container' to network '$network'."
    docker network connect $network $mongodb_container
else
    echo "MongoDB container '$mongodb_container' is already connected to network '$network'."
fi

# Create key-pair
if [ -f "$key_path" ] && [ -f "$key_path.pub" ]; then
    echo "Key pair already exists at $key_path and $key_path.pub"
else
    # Generate the key pair without user interaction
    ssh-keygen -t rsa -b 4096 -q -N "" -f "$key_path"

    # Confirm the key generation
    if [ $? -eq 0 ]; then
        echo "Key pair generated successfully at:"
        echo "Private Key: $key_path"
        echo "Public Key: $key_path.pub"
    else
        echo "Failed to generate key pair."
        exit 1
    fi
fi


# # Jenkins setup

# jenkins_container="jenkins-server"
# jenkins_port=8080
# jenkins_home="jenkins_home"

# # Ensure Jenkins container is running
# if docker ps -a --format '{{.Names}} {{.State}}' | grep -q "^$jenkins_container "; then
#     if docker ps --format '{{.Names}}' | grep -q "^$jenkins_container$"; then
#         echo "Jenkins container '$jenkins_container' is running."
#     else
#         echo "Starting Jenkins container '$jenkins_container'."
#         docker start $jenkins_container
#     fi
# else
#     echo "Creating Jenkins container '$jenkins_container'."
#     docker run -d \
#         --name $jenkins_container \
#         -p $jenkins_port:8080 \
#         -v $jenkins_home:/var/jenkins_home \
#         -v /var/run/docker.sock:/var/run/docker.sock \
#         jenkins/jenkins:lts
# fi

# # Wait for Jenkins to start
# echo "Waiting for Jenkins to initialize (60 seconds)..."
# sleep 60

# # Trigger Jenkins pipeline via REST API
# jenkins_url="http://localhost:$jenkins_port"
# job_name="MyPipeline"
# api_token="<your-api-token>"
# username="<your-username>"

# echo "Triggering Jenkins pipeline..."
# curl -X POST "$jenkins_url/job/$job_name/build" \
#      --user "$username:$api_token"

# echo "Setup complete."
