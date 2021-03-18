#!/bin/bash

# String parameter RELEASE
#   format: yyyy.mm (e.g., 2021.04)

# String parameter JIRA_PROJECT_NAME
#   Default value: PXP

# String parameter JIRA_USER_IDS
#   Default value: 5d9e166df8c67f0dbff6f171,5bedb75065b6ad1237756b4d,5f6baae326269700699b0bb5

# String parameter JIRA_SVC_ACCOUNT
#   Default value: ctds.qa.automation@gmail.com


# JIRA_API_TOKEN
# obtained through Jenkins credentials

export http_proxy=http://cloud-proxy.internal.io:3128
export https_proxy=http://cloud-proxy.internal.io:3128
export no_proxy=localhost,127.0.0.1,localaddress,169.254.169.254,.internal.io,logs.us-east-1.amazonaws.com

python3.6 -m pip install jira --user
python3.6 gen3release-sdk/release_jiras.py
