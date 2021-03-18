#!/bin/bash

# String parameter PR_TITLE
#   e.g., ACCT RELEASE

# String parameter SOURCE_REPO_AND_ENVIRONMENT
#   e.g., gitops-qa/qa-acct.planx-pla.net

# String parameter TARGET_REPO_AND_ENVIRONMENT
#   e.g., cdis-manifest/acct.bionimbus.org

export http_proxy=http://cloud-proxy.internal.io:3128
export https_proxy=http://cloud-proxy.internal.io:3128
export no_proxy=localhost,127.0.0.1,localaddress,169.254.169.254,.internal.io,logs.us-east-1.amazonaws.com

git clone https://github.com/uc-cdis/gitops-qa.git
git clone https://github.com/uc-cdis/cdis-manifest.git

export PATH=$PATH:/home/jenkins/.local/bin:/home/jenkins/.local/lib
python3.6 -m pip install poetry --user
python3.6 -m pip install pygithub --user
python3.6 -m pip install ruamel.yaml --user

python3.6 -m pip uninstall gen3release -y

cd gen3release-sdk
python3.6 -m poetry build

wheel_file=$(ls dist | grep whl | tail -n1)

python3.6 -m pip install dist/${wheel_file} --user

gen3release copy -s ${WORKSPACE}/${SOURCE_REPO_AND_ENVIRONMENT} -e ${WORKSPACE}/${TARGET_REPO_AND_ENVIRONMENT} -pr "${PR_TITLE} $(date +%s)"
