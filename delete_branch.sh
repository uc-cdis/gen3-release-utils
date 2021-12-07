#!bin/bash

if [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ "$#" -ne 2 ]; then
  echo "------------------------------------------------------------------------------"
  echo "Usage - delete_branch <target_branch>"
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

repo_list="repo_list.txt"
while IFS= read -r repo; do
    echo "Cloning the repo .."
    git clone "${urlPrefix}${repo}"
    cd "${repo}" || exit 1
    git checkout master
    result=$(git push origin --delete "${targetBranchName}")
    RC=$?
    if [ $RC -ne 0 ]; then
      echo "$result"
      exit 1
    fi
    cd ..
    quayImageStatus=$(curl ${quayURL}/${repo}/tag/${targetBranchName}/images)
    echo "${quayImageStatus}"
    if [ $quayImageStatus -eq 200 ]; then
      echo "The ${targetBranchName} image exists"
      curl -X DELETE ${quayURL}/${repo}/tag/${targetBranchName}/images
    else
      echo "The ${targetBranchName} doesnot exist"

done < "$repo_list"
