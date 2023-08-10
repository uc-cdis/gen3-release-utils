#!/bin/bash

# checkout gen3-release-utils
# checkout cloud-automation

# String parameter RELEASE_VERSION
#   e.g., 2021.04

set -e
set -x

mkdir -p another_repo
cd another_repo
git clone https://github.com/uc-cdis/cloud-automation.git
cd ..
export GEN3_HOME=another_repo/cloud-automation && source "$GEN3_HOME/gen3/gen3setup.sh"

export KUBECTL_NAMESPACE="default"

g3kubectl get configmap global
webhook_url=$(g3kubectl get configmap global -o jsonpath={.data.ci_test_notifications_webhook})

git clone https://github.com/uc-cdis/cloud-automation.git

# setup gen3 CLI
export GEN3_HOME=$WORKSPACE/cloud-automation
source $GEN3_HOME/gen3/lib/utils.sh
source $GEN3_HOME/gen3/gen3setup.sh

repo_list="repo_list.txt"
while IFS= read -r repo; do
  echo "pushing ${repo} img to AWS ECR..."
  IMG_TO_PUSH="$repo"
  if [ "$repo" == "pelican" ]; then
      echo "Found a repo called pelican"
      IMG_TO_PUSH="pelican-export"
  elif [ "$repo" == "docker-nginx" ]; then
      echo "Found a repo called docker-nginx"
      IMG_TO_PUSH="nginx"
  elif [ "$repo" == "cdis-data-client" ]; then
      echo "Found a repo called cdis-data-client"
      echo "there is no docker img for this repo. Ignore..."
      continue
  elif [ "$repo" == "gen3-fuse" ]; then
      echo "Found a repo called gen3-fuse"
      IMG_TO_PUSH="gen3fuse-sidecar"
  elif [ "$repo" == "cloud-automation" ]; then
      echo "Found a repo called cloud-automation"
      IMG_TO_PUSH="awshelper"
  elif [ "$repo" == "sower-jobs" ]; then
      echo "iterate through list ['metadata-manifest-ingestion', 'get-dbgap-metadata', 'manifest-indexing', 'download-indexd-manifest']"
      sower_jobs=(metadata-manifest-ingestion get-dbgap-metadata manifest-indexing download-indexd-manifest)
      for sowerjob in "${sower_jobs[@]}"; do
        IMG_TO_PUSH="$sowerjob"
        tag="$RELEASE_VERSION"

        set +e
        gen3 ecr update-policy gen3/$IMG_TO_PUSH
        gen3 ecr quay-sync $IMG_TO_PUSH $tag
        RC=$?
        if [ $RC -ne 0  ]; then
          echo "The Image is BROKEN\!"
          webhook_url=$(g3kubectl get configmap global -o jsonpath={.data.ci_test_notifications_webhook})
          curl -X POST --data-urlencode "payload={\"channel\": \"#gen3-qa-notifications\", \"username\": \"release-automation-watcher\", \"text\": \"THE IMAGE ${IMG_TO_PUSH} CANNOT BE PUSHED TO AWS ECR :red_circle: WHOEVER OWNS THIS IMAGE CAN YOU PLEASE INVESTIGATE?? \", \"icon_emoji\": \":facepalm:\"}" $webhook_url
         exit 1
       else
        echo "Successful gen3 ecr quay-sync $IMG_TO_PUSH $tag"
      fi
      set -e
    done

    # move to the next repo
    continue
  elif [ "$repo" == "ACCESS-backend" ]; then
      echo "Found a repo called ACCESS-backend"
      IMG_TO_PUSH="access-backend"
  fi

  tag="$RELEASE_VERSION"

  set +e
  gen3 ecr update-policy gen3/$IMG_TO_PUSH
  gen3 ecr quay-sync $IMG_TO_PUSH $tag
  RC=$?
  if [ $RC -ne 0  ]; then
    echo "The Image is BROKEN\!"
    curl -X POST --data-urlencode "payload={\"channel\": \"#gen3-qa-notifications\", \"username\": \"release-automation-watcher\", \"text\": \"THE IMAGE ${IMG_TO_PUSH} CANNOT BE PUSHED TO AWS ECR :red_circle: WHOEVER OWNS THIS IMAGE CAN YOU PLEASE INVESTIGATE?? \", \"icon_emoji\": \":facepalm:\"}" $webhook_url
    exit 1
  else
    echo "Successful gen3 ecr quay-sync $IMG_TO_PUSH $tag"
  fi
  set -e
done < "$repo_list"
