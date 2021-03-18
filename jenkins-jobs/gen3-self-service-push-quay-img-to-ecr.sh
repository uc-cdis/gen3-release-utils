/*
  String parameter SERVICE_NAME
    e.g., fence

  String parameter QUAY_VERSION
    e.g., 4.23.5
*/
#!/bin/bash

set -e

export KUBECTL_NAMESPACE="$TARGET_ENVIRONMENT"

# setup gen3 CLI
export GEN3_HOME=$WORKSPACE/cloud-automation
source $GEN3_HOME/gen3/gen3setup.sh

gen3 ecr quay-sync ${SERVICE_NAME} ${QUAY_VERSION}
