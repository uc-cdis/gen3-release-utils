#!/bin/bash +x

# checkout gen3-release-utils

# String parameter RELEASE_VERSION
#   e.g., 2021.04

set -e

mkdir -p another_repo
cd another_repo
git clone https://github.com/uc-cdis/cloud-automation.git
cd ..
export GEN3_HOME=another_repo/cloud-automation && source "$GEN3_HOME/gen3/gen3setup.sh"

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
      IMG_TO_PUSH="gen3-client"
  elif [ "$repo" == "gen3-fuse" ]; then
      echo "Found a repo called gen3-fuse"
      IMG_TO_PUSH="gen3fuse-sidecar"
  elif [ "$repo" == "sower-jobs" ]; then
      echo "iterate through list ['metadata-manifest-ingestion', 'get-dbgap-metadata', 'manifest-indexing', 'download-indexd-manifest']"
      sower_jobs=(metadata-manifest-ingestion get-dbgap-metadata manifest-indexing download-indexd-manifest)
      for sowerjob in "${sower_jobs[@]}"; do
		IMG_TO_PUSH="$sowerjob"
        tag="$RELEASE_VERSION"
        gen3 ecr update-policy gen3/$IMG_TO_PUSH
	    gen3 ecr quay-sync $IMG_TO_PUSH $tag
      done

      # move to the next repo
      continue
  elif [ "$repo" == "mariner" ]; then
      echo "iterate through list ['mariner-engine', 'mariner-s3sidecar', 'mariner-server']"
      mariner_images=(mariner-engine mariner-s3sidecar mariner-server)
      for mariner_img in "${mariner_images[@]}"; do
		IMG_TO_PUSH="$mariner_img"
        tag="$RELEASE_VERSION"
        gen3 ecr update-policy gen3/$IMG_TO_PUSH
	    gen3 ecr quay-sync $IMG_TO_PUSH $tag
      done

      # move to the next repo
      continue
  elif [ "$repo" == "ws-storage" ]; then
      echo "Skipping this one as it is not part of 2020.12"

      # move to the next repo
      continue
  fi


  tag="$RELEASE_VERSION"
  gen3 ecr update-policy gen3/$IMG_TO_PUSH
  gen3 ecr quay-sync $IMG_TO_PUSH $tag
done < "$repo_list"