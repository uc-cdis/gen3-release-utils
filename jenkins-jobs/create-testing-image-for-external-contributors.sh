#!/bin/bash

# String parameter OUR_GEN3_SERVICE_REPO_NAME
#   e.g., fence

# String parameter NAME_OF_THE_BRANCH
#   e.g., fence_external_contributor_change1

# String parameter EXTERNAL_REPO_REMOTE_URL
#   e.g., github.com/themarcelor/fence.git

# GITHUB_USERNAME
# GITHUB_TOKEN
# Obtained through Jenkins credentials

git config --global user.email "cdis@uchicago.edu"
git config --global user.name "PlanXCyborg"

OUR_REMOTE_URL="https://github.com/uc-cdis/${OUR_GEN3_SERVICE_REPO_NAME}"

echo "cloning $OUR_REMOTE_URL"
git clone $OUR_REMOTE_URL

pwd

echo "stepping into $OUR_GEN3_SERVICE_REPO_NAME"
cd $OUR_GEN3_SERVICE_REPO_NAME

echo "creating new branch $NAME_OF_THE_BRANCH"
git checkout -b $NAME_OF_THE_BRANCH

echo "changing origin to pull changes from external repo: https://${EXTERNAL_REPO_REMOTE_URL}"
git remote set-url origin https://${EXTERNAL_REPO_REMOTE_URL}

echo "pulling changes from external branch $NAME_OF_THE_BRANCH"
git pull origin $NAME_OF_THE_BRANCH

echo "restore original origin $OUR_REMOTE_URL"
URL_PREFIX="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/uc-cdis/"
git remote set-url origin ${URL_PREFIX}${OUR_GEN3_SERVICE_REPO_NAME}.git

echo "finish branch cloning process but pushing local changes to our repo's branch."
git push --set-upstream origin $NAME_OF_THE_BRANCH
