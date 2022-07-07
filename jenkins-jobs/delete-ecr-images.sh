#!/bin/bash +x

set -e

export KUBECTL_NAMESPACE="$TARGET_ENVIRONMENT"

git clone https://github.com/uc-cdis/cloud-automation.git

# setup gen3 CLI
export GEN3_HOME=$WORKSPACE/cloud-automation
source $GEN3_HOME/gen3/gen3setup.sh

check_image () {
    gen3 ecr describe-image $ECR_REPO $INTEGRATION_BRANCH
    RC=$?
    if [ $RC -ne 0 ]; then
        echo "## The Image $INTEGRATION_BRANCH doesnot exist in repo gen3/$ECR_REPO"
    else
		echo "## The Image exists. So deleting the image .."
        delete_image
    fi
}

delete_image () {
    aws ecr batch-delete-image --repository-name gen3/$ECR_REPO --image-ids imageTag=${INTEGRATION_BRANCH}
    RC=$?
    if [ $RC -ne 0 ]; then
        echo "## The Image $INTEGRATION_BRANCH doesnot exist in repo gen3/$ECR_REPO"
    else
        echo "## The Image $INTEGRATION_BRANCH is deleted from repo gen3/$ECR_REPO"
    fi
}

repo_list="repo_list.txt"
while IFS= read -r repo; do
	echo "---------------"
	echo "##Looking for Image .."
    ECR_REPO="$repo"
    if ["$repo" == "pelican"]; then
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
    elif [ "$repo" == "dataguids.org" ]; then
      ECR_REPO="dataguids"

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
