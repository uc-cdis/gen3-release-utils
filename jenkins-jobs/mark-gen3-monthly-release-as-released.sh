#!/bin/bash

# String parameter RELEASE_NAME
#   e.g., 2021.04

# JIRA_API_TOKEN
# Obtained through the Jenkins credentials

export JIRA_SVC_ACCOUNT="ctds.qa.automation@gmail.com"

python3.6 -m pip install jira==3.0.0.0a0

python3.6 gen3release-sdk/update_jira_release.py
