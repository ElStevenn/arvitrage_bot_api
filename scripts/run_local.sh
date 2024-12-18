#!/bin/bash

container_port=8080
network_name="my_network"
image_name="funding_rate"
container_name="funding_ratev1"

if docker ps -a --format '{{.Names}}' | grep -q "^$container_name$"; then
    docker container stop "$container_name"
    docker container rm "$container_name"
fi

if docker images --format '{{.Repository}}' | grep -q "^$image_name$"; then
    docker image rm "$image_name"
fi

echo "Build and run container? (y/n)"
read response

if [ "$response" == "y" ]; then
    # Build the image
    docker build -t "$image_name" .

    # Run the container
    docker run -d -p "$container_port:$container_port" --name "$container_name" --network "$network_name" "$image_name"
    docker network connect $network_name "$container_name"

    echo "Waiting for container to start..."
    sleep 2

    echo "Show terminal logs? (y/n)"
    read term_qstn

    if [ "$term_qstn" == "y" ]; then
        docker logs --follow "$container_name"
    fi

    # Start
    # terraform apply --var-file="sensitive.tfvars"

    # Destroy
    # terraform destroy -target aws_instance.historical_funding_rate --var-file="sensitive.tfvars"

    # Restart
    # terraform apply -target aws_instance.historical_funding_rate --var-file="sensitive.tfvars" 


else
    echo "Operation aborted."
fi
