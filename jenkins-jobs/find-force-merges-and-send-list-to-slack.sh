#!/bin/bash

# String parameter REPORT_TO_CHANNEL
#   Default value: CT5SC4TU6

# String parameter TARGET_REPO
#   Default value: cdis-manifest

# GITHUB_TOKEN
# QABOT_SLACK_API_TOKEN
# Obtained through Slack credentials

export http_proxy=http://cloud-proxy.internal.io:3128
export https_proxy=http://cloud-proxy.internal.io:3128
export no_proxy=localhost,127.0.0.1,localaddress,169.254.169.254,.internal.io,logs.us-east-1.amazonaws.com

ruby other_scripts/find_force_merges.rb
