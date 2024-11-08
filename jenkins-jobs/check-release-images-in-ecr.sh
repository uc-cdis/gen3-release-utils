#!/bin/bash +x

set -e

export KUBECTL_NAMESPACE="$TARGET_ENVIRONMENT"

git clone https://github.com/uc-cdis/cloud-automation.git

# setup gen3 CLI
export GEN3_HOME=$WORKSPACE/cloud-automation
source $GEN3_HOME/gen3/gen3setup.sh

failed_list=()

check_image () {
    gen3 ecr describe-image $ECR_REPO $RELEASE_VERSION
    RC=$?
    if [ $RC -ne 0 ]; then
        echo "## Release image $RELEASE_VERSION does not exit in repo gen3/$ECR_REPO."
        failed_list+="$ECR_REPO"
    else
        echo "## Release Image $RELEASE_VERSION exists in repo gen3/$ECR_REPO."
    fi
}

repo_list="repo_list.txt"
while IFS= read -r repo; do
    echo "-------------"
    echo "## Looking for Image .. "
    ECR_REPO="$repo"
    if [ "$repo" == "pelican" ]; then
      ECR_REPO="pelican-export"
    elif [ "$repo" == "docker-nginx" ]; then
      ECR_REPO="nginx"
    elif [ "$repo" == "cdis-data-client" ]; then
      echo "Found a repo called cdis-data-client"
      echo "there is no docker img for this repo. Ignore..."
      continue
    elif [ "$repo" == "gen3-fuse" ]; then
      ECR_REPO="gen3fuse-sidecar"
    elif [ "$repo" == "cloud-automation" ]; then
      ECR_REPO="awshelper"
    elif [ "$repo" == "sower-jobs" ]; then
      echo "## iterating through the list ['metadata-manifest-ingestion', 'get-dbgap-metadata', 'manifest-indexing', 'download-indexd-manifest', 'batch-export']"
      sower_job=(metadata-manifest-ingestion get-dbgap-metadata manifest-indexing download-indexd-manifest batch-export)
      for sowerjob in "${sower_job[@]}"; do
        ECR_REPO="$sowerjob"
        set +e
        check_image
        set -e
      done
      continue

    elif [ "$repo" == "ACCESS-backend" ]; then
      ECR_REPO="access-backend"
    fi

    set +e
    check_image
    set -e
done < "$repo_list"

if [[ -n "$failed_list" ]]; then
  echo "### FAILED LIST: ${failed_list}"
  exit 1
fi
