#!/bin/bash

container_port=8080
network_name="my_network"

# remove container
docker container stop funding_rate
docker container rm funding_rate

# remove image
docker image rm image_funding_rate

echo "Build and run container? (y/n)"
read response

if [ "$response" == "y" ]; then
    # Build image
    docker build -t image_funding_rate .

    # Run container
    docker run -d -p 8080:8080 --name funding_rate --network $network_name image_funding_rate

    echo "Show terminal? (y/n)"
    read term_qstn

    if [ "$term_qstn" == y ]; then
        docker logs --follow funding_rate
    fi

else
    echo "OK."
fi