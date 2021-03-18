#!/bin/bash

# Runs every 4th Friday of every month
# Schedule: 0 22 22-28 * 5
# Would last have run at Friday, February 26, 2021 10:00:50 PM UTC; would next run at Friday, March 26, 2021 10:00:50 PM UTC.

# GITHUB_TOKEN
# Obtained through Jenkins credentials

TODAY=`date`
RELEASE_TAG=`date --date="$TODAY +1 month" +%Y.%m`
INTEGRATION_BRANCH_NAME=`date --date="$TODAY +1 month" +"integration%Y%m"`

echo $TODAY
echo $RELEASE_TAG
echo $INTEGRATION_BRANCH_NAME

export GITHUB_USERNAME="atharvar28"

git config --global user.email "cdis@uchicago.edu"

./make_stable_and_tag.sh "${INTEGRATION_BRANCH_NAME}" "${RELEASE_TAG}"
