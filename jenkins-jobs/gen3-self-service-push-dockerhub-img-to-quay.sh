#!/bin/bash

# checkout cloud-automation

# String parameter SOURCE

# String parameter TARGET

# GEN3_QUAY_LOGIN_PASSWORD
# Obtained through Jenkins credentials

set -e

export KUBECTL_NAMESPACE="default"
export HOME=$WORKSPACE

mkdir -p $HOME/Gen3Secrets/quay
echo "$GEN3_QUAY_LOGIN_PASSWORD" > $HOME/Gen3Secrets/quay/login
ls ~/Gen3Secrets/quay/login

# setup gen3 CLI
export GEN3_HOME=$WORKSPACE/cloud-automation
source $GEN3_HOME/gen3/gen3setup.sh

gen3 ecr quaylogin
gen3 ecr dh-quay $SOURCE $TARGET
