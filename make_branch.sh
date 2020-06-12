#!/bin/bash

if [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ "$#" -ne 2 ]; then
  echo "------------------------------------------------------------------------------"
  echo "Usage - make_branch <source_branch> <target_branch>"
  echo ""
  echo "Provide the list of repositories to operate upon in a file named repo_list.txt"
  echo ""
  echo "The script generates the repo urls using urlPrefix and the repo names listed on"
  echo "separate lines in the repo_list.txt file"
  echo "-------------------------------------------------------------------------------"
  exit 0;
fi;

urlPrefix="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/uc-cdis/"
sourceBranchName=$1
targetBranchName=$2

if find . -name "gen3-integration" -type d; then
  echo "Deleting existing gen3-integration folder"
  rm -rf gen3-integration
fi
if mkdir gen3-integration; then
  cd gen3-integration || exit 1
else
  echo "Failed to create the gen3-integration folder. Exiting"
  exit 1
fi

repo_list="../repo_list.txt"
while IFS= read -r repo; do
  echo "### Cutting ${targetBranchName} branch for repo ${repo} ###"
  git clone "${urlPrefix}${repo}"
  cd "${repo}" || exit 1
  git checkout "${sourceBranchName}"
  result=$(git checkout -b "${targetBranchName}")
  RC=$?
  if [ $RC -ne 0 ]; then
    echo "$result"
    exit 1
  fi
  result=$(git push origin "${targetBranchName}")
  RC=$?
  if [ $RC -ne 0 ]; then
    echo "$result"
    exit 1
  fi
  cd ..
done < "$repo_list"

cd ..
echo "### Cleaning up folder gen3-integration ###"
rm -rf gen3-integration
