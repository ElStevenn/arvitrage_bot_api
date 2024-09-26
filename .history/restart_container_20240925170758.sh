#!/bin/bash

# remove container
docker container stop funding_rate
docker container rm funding_rate

# remove image
docker image rm image_funding_rate

echo "Build and run container? (y/n)"
read response

if [ "$response" ==  ]