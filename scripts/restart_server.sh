#!/bin/bash

set -e
set -x  # Enable debug mode

# Variables
DOMAIN="arbibot.paumateu.com"
APP_DIR="/home/ubuntu/arvitrage_bot_api"
CONFIG="/home/ubuntu/scripts/config.json"

SECURITY_PATH="$APP_DIR/src/security"
PRIVATE_KEY="$SECURITY_PATH/secure_key"
PUBLIC_KEY="$SECURITY_PATH/public_key.pub"
IMAGE_NAME="arvitrage_bot_api"
CONTAINER_NAME="arvitrage_bot_api_v1"
NETWORK_NAME="my_network"
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
NGINX_CONF="$NGINX_CONF_DIR/arvitrage_bot_api"

# Ensure directories
sudo mkdir -p "$NGINX_CONF_DIR" "$NGINX_ENABLED_DIR"
mkdir -p "$SECURITY_PATH"

# Generate keys if needed
if [ ! -f "$PRIVATE_KEY" ]; then
    echo "Generating private key..."
    ssh-keygen -t rsa -b 4096 -f "$PRIVATE_KEY" -q -N ""
    echo "Private and public keys have been generated."
fi

# Ensure .env file
[ ! -f "$APP_DIR/src/.env" ] && touch "$APP_DIR/src/.env"

# Stop and remove existing container
echo "Stopping and removing existing Docker container: $CONTAINER_NAME"
docker container stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker container rm "$CONTAINER_NAME" >/dev/null 2>&1 || true

# Update API flag in config if config exists
if [ -f "$CONFIG" ]; then
    echo "Updating API flag in config..."
    jq '.api = false' "$CONFIG" > temp.json && mv temp.json "$CONFIG"
fi

# Update packages and install Nginx and necessary tools (Removed Certbot)
echo "Updating system packages..."
sudo apt-get update -y
sudo apt-get install -y nginx jq

# Allow Nginx through firewall if UFW is enabled
if sudo ufw status | grep -q "Status: active"; then
    echo "Configuring UFW to allow Nginx Full..."
    sudo ufw allow 'Nginx Full' || true
fi

# Create Docker network if it doesn't exist
if ! docker network ls --format '{{.Name}}' | grep -w "$NETWORK_NAME" > /dev/null; then
    echo "Creating Docker network: $NETWORK_NAME"
    docker network create "$NETWORK_NAME"
else
    echo "Docker network '$NETWORK_NAME' already exists."
fi

# Build Docker image
echo "Building Docker image: $IMAGE_NAME"
cd "$APP_DIR" || { echo "App directory not found: $APP_DIR"; exit 1; }
docker build -t "$IMAGE_NAME" .

# Run the container mapped to localhost:8000
echo "Running Docker container: $CONTAINER_NAME"
docker run -d --name "$CONTAINER_NAME" --network "$NETWORK_NAME" -p 127.0.0.1:8000:8080 "$IMAGE_NAME"

# Wait for the container to be ready
echo "Waiting for the Docker container to initialize..."
sleep 5  # Adjust the sleep duration as needed

# Check if the application inside the container is running
if ! curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "Application is not responding on http://127.0.0.1:8000"
    echo "Check Docker container logs for details:"
    docker logs "$CONTAINER_NAME"
    exit 1
fi

echo "Application is running and accessible."

# Create Nginx server block
echo "Configuring Nginx..."
sudo bash -c "cat > $NGINX_CONF" <<EOL
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

# Enable the Nginx configuration
echo "Enabling Nginx configuration..."
sudo ln -sf "$NGINX_CONF" "$NGINX_ENABLED_DIR/arvitrage_bot_api"
sudo rm -f /etc/nginx/sites-enabled/default || true

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

# Restart Nginx to apply changes
echo "Restarting Nginx..."
sudo systemctl restart nginx

# Final Health Check via Nginx
echo "Performing final health check via Nginx..."
if ! curl -s http://$DOMAIN/health > /dev/null; then
    echo "Nginx is unable to proxy to the application. Check Nginx and Docker logs."
    exit 1
fi

echo "Server restart completed successfully. The application is accessible at http://$DOMAIN"
