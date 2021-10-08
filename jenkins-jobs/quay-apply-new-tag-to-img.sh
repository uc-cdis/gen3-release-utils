#!/bin/bash

# login to QUAY
docker login -u="cdis+gen3" -p="${QUAY_API_TOKEN}" quay.io

# pull the existing integration branch image
docker pull quay.io/cdis/${SERVICE_NAME}:${CURRENT_IMG_TAG}
# create a new docker tag locally
docker tag quay.io/cdis/${SERVICE_NAME}:${CURRENT_IMG_TAG} quay.io/cdis/${SERVICE_NAME}:${NEW_IMG_TAG}
# push the same image with a new tag
docker push quay.io/cdis/${SERVICE_NAME}:${NEW_IMG_TAG}

# delete the docker images after the push to avoid filling up the disk space
docker rmi quay.io/cdis/${SERVICE_NAME}:${CURRENT_IMG_TAG}
docker rmi quay.io/cdis/${SERVICE_NAME}:${NEW_IMG_TAG}
