#!/bin/bash

# String parameter RELEASE_VERSION
#   format yyyy.mm (e.g., 2021.04)

# JIRA_API_TOKEN
# Obtained through Jenkins credentials

export JIRA_SVC_ACCOUNT="ctds.qa.automation@gmail.com"

python3 -m pip install jira==2.0

python3 gen3release-sdk/create_jira_project_version.py
