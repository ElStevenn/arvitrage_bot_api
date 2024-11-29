#!/bin/bash

# Sensitive variables
mongo_username=$TF_VAR_mongo_root_password
mongo_password=$TF_VAR_mongo_root_password
infura_apikey=$TF_VAR_infura_api_key
coinmarketcap_apikey=$TF_VAR_coinmarketcap_apikey

# MongoDB Container variables
mongodb_container="mongodb_v1"
network="my_network"
volume="data_volume"
key_path="src/security/secure_key"

# Python container variables
container_port=8080
image_name="funding_rate"
container_name="funding_ratev2"


# Check for required environment variables
if [ -z "$TF_VAR_mongo_root_password" ] || [ -z "$TF_VAR_infura_apikey" ] || [ -z "$TF_VAR_coinmarketcap_apikey" ]; then
    echo "Required environment variables are not set. Please set TF_VAR_mongo_root_password, TF_VAR_infura_api_key, and TF_VAR_coinmarketcap_apikey."
    exit 1
fi


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

# Ensure volume exists
if ! docker volume ls --format '{{.Name}}' | grep -q "^$volume$"; then
    echo "Creating volume '$volume'."
    docker volume create $volume
else
    echo "Docker volume '$volume' already exists."
fi

# Ensure network exists
if ! docker network ls --format '{{.Name}}' | grep -q "^$network$"; then
    echo "Creating network '$network'."
    docker network create $network
else
    echo "Docker network '$network' already exists."
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
        -p 27017:27017 \
        -e MONGO_INITDB_ROOT_USERNAME=$mongo_username \
        -e MONGO_INITDB_ROOT_PASSWORD=$mongo_password \
        mongo --bind_ip 0.0.0.0

fi

docker network connect $network $mongodb_container

mongo_container_ip=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $mongodb_container)
echo "MongoDB container IP address: $mongo_container_ip"

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

# Web3 infrastructure
INFRA_PROJECT_ID=$infura_apikey

EOF
    echo "src/.env file created successfully."
fi

# Build and deploy main image
docker build -t "$image_name" .
docker run -d -p "$container_port:$container_port" --name "$container_name" --network "$network" "$image_name"
docker network connect $network "$container_name"
sleep 2
docker logs --follow "$container_name"
