#!bin/bash

if [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ "$#" -ne 1 ]; then
  echo "------------------------------------------------------------------------------"
  echo "Usage - delete_branch <target-branch-name>"
  echo ""
  echo "Provide the list of repositories to operate upon in a file named repo_list.txt"
  echo ""
  echo "The script generates the repo urls using urlPrefix and the repo names listed on"
  echo "separate lines in the repo_list.txt file"
  echo "-------------------------------------------------------------------------------"
  exit 0;
fi;

urlPrefix="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/uc-cdis/"
quayURL="https://quay.io/api/v1/repository/cdis"
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
      curl -X DELETE -H "Authorization: Bearer ${QUAY_TOKEN}" ${quayURL}/${repo}/tag/${targetBranchName}
      echo "${repo} Image deleted"
    else
      echo "The ${targetBranchName} doesnot exist"
    fi
done < "$repo_list"
