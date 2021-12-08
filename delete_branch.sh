#!bin/bash

urlPrefix="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/uc-cdis/"
quayURL="https://${QUAY_TOKEN}@quay.io/api/v1/repository/cdis"
targetBranchName=$1

if find . -name "gen3-integration-deletion" -type d; then
  echo "Deleting existing gen3-integration-deletion folder"
  rm -rf gen3-integration-deletion
fi
if mkdir gen3-integration-deletion; then
  cd gen3-integration-deletion || exit 1
else
  echo "Failed to create the folder, exiting ..."
  exit 1
fi

repo_list="../repo_list.txt"
while IFS= read -r repo; do
    echo "Cloning the repo .."
    git clone "${urlPrefix}${repo}"
    cd "${repo}" || exit 1
    git checkout master
    result=$(git push origin --delete "${targetBranchName}")
    RC=$?
    if [ $RC -ne 0 ]; then
      echo "$result"
      echo "continuing .."
    fi
    quayImageStatus=$(curl -s -o /dev/null -I -w "%{http_code}" ${quayURL}/${repo}/tag/${targetBranchName}/images)
    echo "${quayImageStatus}"
    if [ $quayImageStatus -eq 200 ]; then
      echo "The ${targetBranchName} image exists"
      curl -X DELETE ${quayURL}/${repo}/tag/${targetBranchName}
    else
      echo "The ${targetBranchName} doesnot exist"
    fi
done < "$repo_list"
