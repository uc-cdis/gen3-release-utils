#!/bin/bash

if [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ "$#" -ne 3 ]; then
  echo "------------------------------------------------------------------------------"
  echo "Usage - generate_release_notes"
  echo ""
  echo "Provide the list of repositories to operate upon in a file named repo_list.txt"
  echo ""
  echo "Ensure env var GITHUB_TOKEN is set with the Github Personal Access Token"
  echo "-------------------------------------------------------------------------------"
  exit 0;
fi;

repoOwner="uc-cdis"
echo "### startDate is ${startDate} ###"
echo "### endDate is ${endDate} ###"
githubAccessToken=$GITHUB_TOKEN

if find . -name "release_notes.md" -type f; then
  echo "Deleting existing release notes"
  rm -f gen3_release_notes.md
fi

touch gen3_release_notes.md
echo "# $releaseName" >> gen3_release_notes.md
echo >> gen3_release_notes.md

repo_list="repo_list.txt"
while IFS= read -r repo; do
  echo "### Getting the release notes for repo ${repo} ###"
  result=$(gen3git --repo "${repoOwner}/${repo}" --github-access-token "${githubAccessToken}" --from-date "${startDate}" gen --to-date "${endDate}" --markdown)
  RC=$?
  if [ $RC -ne 0 ]; then
    echo "$result"
    exit 1
  fi
  if [[ $(wc -l < release_notes.md) -ge 3 ]]; then
    cat release_notes.md
    cat release_notes.md >> gen3_release_notes.md
  fi
done < "$repo_list"
