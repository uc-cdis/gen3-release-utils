#!/bin/bash

# Runs everyday at 9 AM UTC
# Schedule: H 8 * * *
# Would last have run at Wednesday, March 17, 2021 8:53:30 AM UTC; would next run at Thursday, March 18, 2021 8:53:30 AM UTC.

# Archives: *.txt

git clone https://github.com/uc-cdis/cloud-automation.git
export GEN3_HOME=cloud-automation
export KUBECTL_NAMESPACE=qaplanetv1

source $GEN3_HOME/gen3/gen3setup.sh

g3kubectl get ns | grep -v jupyter | grep -v sftp | grep -v grafana | grep -v prometheus | grep -v logging | grep -v loki | grep -v jenkins | grep -v kube > ls_environments.txt
