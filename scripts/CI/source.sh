#!/bin/bash

config="/home/ubuntu/scripts/config.json"

# Variables
network_name="my_network"
volume_name="my_volume"
mongo_image_name="mongodb"
mongodb_container="mongodb_v1"


# Configure
if [ -f "$config" ]; then
    echo "config file found."
    if [[ -s "$config" ]]; then

        # Read the config file
        NETWORK=$(jq -r '.network' "$config")
        VOLUME=$(jq -r '.volume' "$config")
        MONGO=$(jq -r '.mongodb' "$config")
        FIRST_TIME=$(jq -r '.first_time' "$config")

        if [[ "$NETWORK" == "false" ]]; then
            echo "Creating network..."
            docker network create --driver bridge --subnet 172.16.0.0/16 $network_name

            jq '.network = true' "$config" > temp.json && mv temp.json "$config"
        fi

        if [[ "$VOLUME" == "false" ]]; then
            echo "Creating volume..."
            docker volume create --driver local --opt $volume_name

            jq '.volume = true' "$config" > temp.json && mv temp.json "$config"
        fi

        if [[ "$MONGO" == "false" ]]; then
            echo "Creating mongodb container..."
            docker pull mongo:lastest
            docker run -d \
                --name $mongodb_container \
                --network $network_name \
                --volume $volume_name:/data/db \
                -e MONGO_INITDB_ROOT_USERNAME=test_user \
                -e MONGO_INITDB_ROOT_PASSWORD=test_password \
                -p 27017:27017 \
                mongo

            jq '.mongodb = true' "$config" > temp.json && mv temp.json "$config"
        fi

        if [[ "$FIRST_TIME" == "true" ]]; then
            echo "First time setup..."
            git clone https://github.com/ElStevenn/arvitrage_bot_api.git
            cd arvitrage_bot_api

            jq '.first_time = false' "$config" > temp.json && mv temp.json "$config"
        else
            git pull origin main
            cd arvitrage_bot_api
        fi

    else
        echo "config file is empty."
        exist 1
    fi

else
    echo "config file not found."
    exist 1
fi