#!/bin/bash

# String parameter PR_TITLE
#   e.g., BDCAT RELEASE

# String parameter SOURCE_ENVIRONMENT
#   e.g., preprod.gen3.biodatacatalyst.nhlbi.nih.gov

# String parameter TARGET_ENVIRONMENT
#   e.g., gen3.biodatacatalyst.nhlbi.nih.gov

# String parameter REPO_NAME
#   e.g., cdis-manifest


# GITHUB_TOKEN
# Obtained through Jenkins credentials

export http_proxy=http://cloud-proxy.internal.io:3128
export https_proxy=http://cloud-proxy.internal.io:3128
export no_proxy=localhost,127.0.0.1,localaddress,169.254.169.254,.internal.io,logs.us-east-1.amazonaws.com

git clone https://github.com/uc-cdis/${REPO_NAME}.git

export PATH=$PATH:/home/jenkins/.local/bin:/home/jenkins/.local/lib

pip3 install -U pip --user
pip3 install --editable git+https://github.com/uc-cdis/release-helper.git@gen3release#egg=gen3git --user
pip3 install pygit2 --user

python3.8 -m pip install poetry --user
python3.8 -m pip install pygithub --user
python3.8 -m pip install ruamel.yaml --user

python3.8 -m pip uninstall gen3release -y

cd gen3release-sdk
python3.8 -m poetry build

wheel_file=$(ls dist | grep whl | tail -n1)

poetry install

poetry run gen3release copy -s ${WORKSPACE}/${REPO_NAME}/${SOURCE_ENVIRONMENT} -e ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT} -pr "${PR_TITLE} $(date +%s)"
