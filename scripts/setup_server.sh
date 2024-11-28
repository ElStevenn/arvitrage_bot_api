#!/bin/bash

# Declare variables
mongodb_container="mongodb_v1"
network="my_network"
volume="data_volume"
key_path="src/security/secure_key"
mongo_username=""
mongo_password=""

# Container variables
container_port=8080
image_name="funding_rate"
container_name="funding_ratev1"

install_docker() {
    # Function to install Docker

    echo "Docker is not installed. Installing Docker and dependencies..."
    sudo apt-get update -y
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

    echo "Enter MongoDB username:"
    read mongo_username

    echo "Enter MongoDB password:"
    read -s mongo_password

    docker run -d \
        --name $mongodb_container \
        --network $network \
        --volume $volume:/data/db \
        -p 27017:27017 \
        -e MONGO_INITDB_ROOT_USERNAME=$mongo_username \
        -e MONGO_INITDB_ROOT_PASSWORD=$mongo_password \
        mongo --bind_ip 0.0.0.0

fi

docker network connect $network $mongodb_container


# Obtain MongoDB container IP address
mongo_container_ip=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $mongodb_container)
echo "MongoDB container IP address: $mongo_container_ip"

# Ensure the directory for the key exists
mkdir -p "$(dirname "$key_path")"

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

# Ask for required sensitive variables
echo "Enter CoinMarketCap API key:"
read coinmarketcap_apikey

# Create src/.env file
if [ -f "src/.env" ]; then
    echo "src/.env file already exists."
else
    echo "Creating src/.env file..."
    cat <<EOF > src/.env
# APIKEYS of punctual APIs
COINMARKETCAP_APIKEY=$coinmarketcap_apikey

# MONGODB CONNECTION
MONGODB_URL=$mongo_container_ip
MONGO_USER=$mongo_username
MONGO_PASSWD=$mongo_password
EOF
    echo "src/.env file created successfully."
fi

local_ip="127.0.0.1"
external_ip=$(curl -s http://checkip.amazonaws.com)
local_mongodb_uri="mongodb://$mongo_username:$mongo_password@$local_ip:27017/admin"
external_mongodb_uri="mongodb://$mongo_username:$mongo_password@$external_ip:27017/admin"
container_mongodb_uri="mongodb://$mongo_username:$mongo_password@$mongo_container_ip:27017/admin"

# Display the MongoDB URIs
echo "MongoDB Connection URIs:"
echo "Local: $local_mongodb_uri"
echo "External: $external_mongodb_uri"
echo "Container IP: $container_mongodb_uri"

echo ""
echo ""

echo "Do you want to deploy the app? (y/n)"
read deplo

# Build and deploy application
if [ "$deplo" == "y" ];then
    clear
    docker build -t $image_name .
    docker run -d -p $container_port:$container_port --name $container_name --network $network $image_name
    docmer network connect $network $container_name
    
    echo "app deployed at http://$external_mongodb_uri:8080"
    echo "Do you want to setup the essential data (y/n)"
    read setup

    

    if [ "$setup" == "y" ]; then
        echo "Setting up essential data..."
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
