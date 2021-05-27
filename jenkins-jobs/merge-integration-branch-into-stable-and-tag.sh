#!/bin/bash

# String parameter INTEGRATION_BRANCH_NAME
#   Default value: integration20210xx

# String parameter RELEASE_VERSION
#   Default value: 2021.xx

# GITHUB_USERNAME
# GITHUB_TOKEN
# Obtained through Jenkins credentials

git config --global user.email "cdis@uchicago.edu"

./make_stable_and_tag.sh "${INTEGRATION_BRANCH_NAME}" "${RELEASE_VERSION}"
