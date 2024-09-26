#!/bin/bash

cntainer_port=8080

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
    docker run -d -p 8080:8080 --name 

else
    echo "OK."
fi