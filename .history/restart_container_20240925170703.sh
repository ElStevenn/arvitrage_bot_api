#!/bin/bash

# remove container
docker container stop funding_rate
docker container rm funding_rate

# remove image
docker image rm 