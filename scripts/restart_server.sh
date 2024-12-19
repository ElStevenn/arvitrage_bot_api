#!/bin/bash
set -e
set -x  # Enable debug mode for detailed logging

# Variables
DOMAIN="arbibot.paumateu.com"
APP_DIR="/home/ubuntu/arvitrage_bot_api"    
IMAGE_NAME="arvitrage_bot_api"             
CONTAINER_NAME="arvitrage_bot_api_v1"     
NETWORK_NAME="my_network"

# Stop and remove existing Docker container if it exists
echo "Stopping existing Docker container..."
docker container stop "$CONTAINER_NAME" >/dev/null 2>&1 || true

echo "Removing existing Docker container..."
docker container rm "$CONTAINER_NAME" >/dev/null 2>&1 || true

# (Optional) Pull the latest code or rebuild if necessary
echo "Pulling latest code from repository..."
cd "$APP_DIR" || exit 1
git pull origin main  # Adjust if using a different branch

# Rebuild the Docker image (if there are code changes)
echo "Rebuilding Docker image..."
docker build -t "$IMAGE_NAME" .

# Run the Docker container mapped to localhost:8000:8080
echo "Starting new Docker container..."
docker run -d --name "$CONTAINER_NAME" --network "$NETWORK_NAME" -p 127.0.0.1:8000:8080 "$IMAGE_NAME"

# Reload Nginx to ensure it detects the new container instance
echo "Testing Nginx configuration..."
sudo nginx -t

echo "Reloading Nginx..."
sudo systemctl reload nginx

echo "Server restart complete. Your application is now running behind Nginx at https://$DOMAIN/"
