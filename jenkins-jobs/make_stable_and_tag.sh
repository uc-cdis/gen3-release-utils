#!/bin/bash

echo "### ## name_of_the_branch: $GIT_BRANCH"

# if [[ "$GIT_BRANCH" == "origin/master" ]]; then
#  echo "all good. proceed..."
# else
#  echo "ABORT\! Not a master branch!!! If you are running this locally, declare the GIT_BRANCH environment variable accordingly."
#  exit 1
# fi

if [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ "$#" -ne 2 ]; then
  echo "------------------------------------------------------------------------------"
  echo "Usage - make_stable_and_tag <integrationBranchName> <releaseTagName>"
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
tagName=$2
targetBranchName="stable"

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
  echo "### Pulling ${targetBranchName} branch into the stable branch for repo ${repo} ###"
  git clone "${urlPrefix}${repo}"
  cd "${repo}" || exit 1
  git ls-remote --heads ${urlPrefix}${repo} ${targetBranchName} | grep ${BRANCH} >/dev/null
  if [ "$?" == "0" ]; then
    git checkout "${targetBranchName}"
    git pull origin "${targetBranchName}"
  else
    git checkout -b "${targetBranchName}"
  fi
  git checkout "${targetBranchName}"
  git config user.name "${GITHUB_USERNAME}"
  result=$(git pull origin "${sourceBranchName}")
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
  result=$(git tag "${tagName}" -a -m "Gen3 Core Release ${tagName}" 2>&1)
  if [[ "$result" == *"already exists"* ]]; then
    echo "meh. Tag ${tagName} already exists for repo ${repo}... skipping it."
    continue
  fi

  RC=$?
  if [ $RC -ne 0 ]; then
    echo "$result"
    exit 1
  fi
  result=$(git push origin --tags)
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
