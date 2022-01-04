/*
  String parameter SERVICE_NAME
    e.g., fence

  String parameter QUAY_VERSION
    e.g., 4.23.5
*/
#!/bin/bash

set -e
set -x

export KUBECTL_NAMESPACE="$TARGET_ENVIRONMENT"

# setup gen3 CLI
export GEN3_HOME=$WORKSPACE/cloud-automation
source $GEN3_HOME/gen3/gen3setup.sh

repoExist=$(aws ecr describe-repositories | jq -r .repositories[].repositoryName | grep ${SERVICE_NAME})
if [[ -z repoExist ]]; then
  echo "create new ECR repo for ${SERVICE_NAME} ..."
	gen3 ecr create-repository ${SERVICE_NAME}
  echo "The Repo ${SERViCE_NAME} is created in AWS ECR"
fi
gen3 ecr quay-sync ${SERVICE_NAME} ${QUAY_VERSION}

echo "The Image is pushed to ECR"
